"""Extract syntax evidence, without claiming Rust name resolution or macro expansion."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import tree_sitter_rust
from tree_sitter import Language, Node, Parser

Record = dict[str, Any]
HTTP_CALLS = {"get", "post", "put", "delete", "patch", "get_without_response_decoding"}
SEND_CALLS = {"send_bpi_payload", "send_bpi_optional_payload", "send_bpi_envelope", "send_request"}


def text(node: Node | None) -> str:
    return node.text.decode("utf-8") if node is not None and node.text else ""


def attributes(node: Node) -> list[str]:
    result = []
    previous = node.prev_named_sibling
    while previous and previous.type in {"attribute_item", "line_comment", "block_comment"}:
        if previous.type == "attribute_item":
            result.append(text(previous))
        previous = previous.prev_named_sibling
    return list(reversed(result))


def nodes(node: Node) -> Iterator[Node]:
    """Skip explicit test-only declarations, including their entire subtree."""
    if any(re.fullmatch(r"#\[\s*cfg\s*\(\s*test\s*\)\s*\]", a) for a in attributes(node)):
        return
    if node.type == "mod_item" and text(node.child_by_field_name("name")) == "tests":
        return
    yield node
    for child in node.named_children:
        yield from nodes(child)


def literal(node: Node | None) -> str | None:
    if node is None:
        return None
    if node.type == "string_literal":
        try:
            value = json.loads(text(node))
        except ValueError:
            return None  # Rust-specific escapes need review.
        return value if isinstance(value, str) else None
    if node.type == "raw_string_literal":
        contents = [child for child in node.named_children if child.type == "string_content"]
        return text(contents[0]) if contents else ""
    return None


def parent_of_type(node: Node, kind: str) -> Node | None:
    parent = node.parent
    while parent:
        if parent.type == kind:
            return parent
        parent = parent.parent
    return None


def visibility(node: Node) -> str:
    return next((text(c) for c in node.named_children if c.type == "visibility_modifier"), "")


def call_parts(node: Node) -> tuple[str, str, list[Node]]:
    function = node.child_by_field_name("function")
    args = node.child_by_field_name("arguments")
    # Generic method calls wrap their function in generic_function.
    if function and function.type == "generic_function":
        function = function.child_by_field_name("function")
    if function and function.type == "field_expression":
        name = text(function.child_by_field_name("field"))
        receiver = text(function.child_by_field_name("value"))
    else:
        name, receiver = text(function), ""
    return name, receiver, args.named_children if args else []


def extract_file(path: Path, root: Path, domains: set[str]) -> Record:
    source = path.read_bytes()
    tree = Parser(Language(tree_sitter_rust.language())).parse(source)
    if tree.root_node.has_error:
        errors = [
            str(n.start_point.row + 1)
            for n in nodes(tree.root_node)
            if n.type == "ERROR" or n.is_missing
        ]
        raise ValueError(f"Rust syntax error: {path.relative_to(root)} lines {','.join(errors)}")
    relative = path.relative_to(root).as_posix()
    domain = path.relative_to(root / "src").parts[0]
    result: Record = {"path": relative, "methods": [], "types": [], "constants": [], "macros": []}
    if domain not in domains:
        return result
    for node in nodes(tree.root_node):
        name = text(node.child_by_field_name("name"))
        location = {"path": relative, "line": node.start_point.row + 1}
        # Only module-level constants: local shadowing must not masquerade as endpoint resolution.
        if node.type == "const_item" and node.parent and node.parent.type == "source_file":
            value = literal(node.child_by_field_name("value"))
            if value is not None:
                result["constants"].append({"name": name, "value": value, "domain": domain})
        if node.type in {"struct_item", "enum_item", "type_item"}:
            if parent_of_type(node, "function_item"):
                continue
            fields = []
            for field in nodes(node):
                if field.type == "field_declaration":
                    fields.append(
                        {
                            "name": text(field.child_by_field_name("name")),
                            "rust_type": text(field.child_by_field_name("type")),
                            "attributes": attributes(field),
                        }
                    )
            result["types"].append(
                {
                    "id": f"{relative}:{node.start_point.row + 1}:{name}",
                    "name": name,
                    "domain": domain,
                    "kind": node.type,
                    "visibility": visibility(node),
                    "attributes": attributes(node),
                    "declaration": text(node),
                    "fields": fields,
                    "source": location,
                    "migration_status": "not_generated",
                }
            )
        if node.type == "macro_invocation" and not parent_of_type(node, "function_item"):
            result["macros"].append({"source": location, "expression": text(node)})
        if node.type != "function_item" or visibility(node) != "pub":
            continue
        if parent_of_type(node, "function_item"):
            continue
        modifiers = next(
            (text(c) for c in node.named_children if c.type == "function_modifiers"), ""
        )
        if "async" not in modifiers.split():
            continue
        body = node.child_by_field_name("body")
        impl = parent_of_type(node, "impl_item")
        owner = text(impl.child_by_field_name("type")) if impl else None
        calls, requests, bindings, labels = [], [], [], []
        for item in nodes(body) if body else []:
            if item.type != "call_expression":
                continue
            call, receiver, args = call_parts(item)
            calls.append(call)
            if call in HTTP_CALLS and (
                receiver in {"self", "client"} or receiver.endswith(".client")
            ):
                requests.append(
                    {
                        "method": "GET"
                        if call == "get_without_response_decoding"
                        else call.upper(),
                        "expression": text(args[0]) if args else "",
                        "literal_url": literal(args[0]) if args else None,
                        "line": item.start_point.row + 1,
                    }
                )
            if call in {"query", "form", "json", "multipart"}:
                bindings.append({"location": call, "expression": ", ".join(text(a) for a in args)})
            if call in SEND_CALLS and args:
                value = literal(args[0])
                if value:
                    labels.append(value)
        ancestors = []
        parent = node.parent
        while parent:
            ancestors.extend(attributes(parent))
            parent = parent.parent
        result["methods"].append(
            {
                "id": f"{relative}:{node.start_point.row + 1}:{owner or 'free'}::{name}",
                "domain": domain,
                "name": name,
                "owner": owner,
                "source": location,
                "signature": source[node.start_byte : body.start_byte].decode().strip()
                if body
                else text(node),
                "return_type": text(node.child_by_field_name("return_type")),
                "attributes": attributes(node),
                "enclosing_attributes": ancestors,
                "request_calls": requests,
                "parameter_bindings": bindings,
                "contract_labels": sorted(set(labels)),
                "calls": sorted(set(calls)),
                "control_flow": sorted(
                    {
                        n.type
                        for n in nodes(body)
                        if n.type
                        in {
                            "if_expression",
                            "match_expression",
                            "for_expression",
                            "while_expression",
                            "loop_expression",
                            "closure_expression",
                        }
                    }
                )
                if body
                else [],
                "python_method_suggestion": f"client.{domain}.{name}",
                "migration_status": "not_generated",
            }
        )
    return result
