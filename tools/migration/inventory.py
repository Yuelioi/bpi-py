"""Join contract evidence to Rust syntax and produce a deterministic migration report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

from .rust import Record, extract_file


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def inside(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes source root: {path}")
    return resolved


def read_contracts(root: Path) -> tuple[list[Record], list[Path]]:
    contracts, inputs, names = [], [], set()
    for path in sorted((root / "tests/contracts").rglob("contract.json")):
        inside(root, path)
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data["name"]
        if name in names:
            raise ValueError(f"Duplicate contract ID: {name}")
        names.add(name)
        inputs.append(path)
        fixtures = []
        for case in data.get("cases", []):
            response = case.get("response", {})
            if not response.get("fixture"):
                continue
            fixture = inside(root, path.parent / response["fixture"])
            if not fixture.is_file():
                raise ValueError(f"Missing fixture for {name}: {response['fixture']}")
            inputs.append(fixture)
            fixtures.append(
                {
                    "case": case["name"],
                    "path": fixture.relative_to(root).as_posix(),
                    "kind": response.get("fixture_kind"),
                    "rust_model": response.get("rust_model"),
                    "http_status": response.get("http_status"),
                    "api_code": response.get("api_code"),
                }
            )
        contracts.append(
            {
                "id": name,
                "domain": data["module"],
                "path": path.relative_to(root).as_posix(),
                "schema_version": data.get("schema_version"),
                "risk": data.get("risk"),
                "status": data.get("status"),
                "profiles": data.get("profiles", []),
                "request": data.get("request"),
                "requests": [data["request"]]
                if "request" in data
                else [step["contract"]["request"] for step in data["steps"]],
            "steps": data.get("steps", []),
            "cases": data.get("cases", []),
                "fixtures": fixtures,
                "provenance": data.get("provenance", {}),
                "migration_status": "not_generated",
            }
        )
    if not contracts:
        raise ValueError("No contracts found")
    return contracts, inputs


def associate(methods: list[Record], contracts: list[Record], files: list[Record]) -> None:
    for method in methods:
        domain_files = [
            f for f in files if any(c["domain"] == method["domain"] for c in f["constants"])
        ]
        for request in method["request_calls"]:
            expression = request["expression"]
            constants = [
                {**c, "path": f["path"]}
                for f in domain_files
                for c in f["constants"]
                if c["name"] == expression
            ]
            # This is syntax evidence only; imported, shadowed and cfg constants need review.
            local = [c for c in constants if c["path"] == method["source"]["path"]]
            candidates = local or constants
            urls = sorted({c["value"] for c in candidates if c["value"].startswith("https://")})
            request["url_candidates"] = [request["literal_url"]] if request["literal_url"] else urls
            request["resolution"] = (
                "literal"
                if request["literal_url"]
                else "file_constant_candidate"
                if local
                else "domain_constant_candidate"
                if candidates
                else "unresolved"
            )
        links = []
        for contract in contracts:
            if contract["domain"] != method["domain"]:
                continue
            evidence = None
            if contract["id"] in method["contract_labels"]:
                evidence = "contract_label"
            elif any(
                expected["url"] in req["url_candidates"]
                and expected["method"].upper() == req["method"]
                for req in method["request_calls"]
                for expected in contract["requests"]
            ):
                evidence = "url_candidate"
            if evidence:
                links.append({"contract": contract["id"], "evidence": evidence})
        method["contracts"] = links
        method["risk_from_contracts"] = sorted(
            {
                c["risk"]
                for c in contracts
                if any(link["contract"] == c["id"] for link in links) and c["risk"] is not None
            }
        )
        calls = method["calls"]
        method["signing_evidence"] = [c for c in calls if "wbi" in c or "ticket" in c]
        method["auth_evidence"] = [
            c for c in calls if "csrf" in c or "cookie" in c or "account" in c
        ]
        reasons = []
        if not links:
            reasons.append("no_contract_match")
        if links and not any(link["evidence"] == "contract_label" for link in links):
            reasons.append("url_match_requires_review")
        if len(method["request_calls"]) != 1:
            reasons.append("indirect_or_multiple_requests")
        if any(not r["url_candidates"] for r in method["request_calls"]):
            reasons.append("unresolved_url")
        if any(len(r["url_candidates"]) > 1 for r in method["request_calls"]):
            reasons.append("ambiguous_url")
        exact_contracts = [
            c
            for c in contracts
            if c["domain"] == method["domain"] and c["id"] in method["contract_labels"]
        ]
        if (
            method["request_calls"]
            and exact_contracts
            and not any(
                expected["url"] in req["url_candidates"]
                and expected["method"].upper() == req["method"]
                for c in exact_contracts
                for expected in c["requests"]
                for req in method["request_calls"]
            )
        ):
            reasons.append("label_request_mismatch")
        if method["control_flow"]:
            reasons.append("custom_control_flow")
        if not ({"send_bpi_payload", "send_bpi_optional_payload"} & set(calls)):
            reasons.append("custom_response_handling")
        if "multipart" in calls:
            reasons.append("multipart")
        if any(
            r not in {"public-read", "authenticated-read", "private-read"}
            for r in method["risk_from_contracts"]
        ):
            reasons.append("session_or_mutation_contract")
        method["review_reasons"] = reasons
        method["automation"] = "request_shell_candidate" if not reasons else "manual_review"
    for contract in contracts:
        links = [
            {"method": m["id"], "evidence": link["evidence"]}
            for m in methods
            for link in m["contracts"]
            if link["contract"] == contract["id"]
        ]
        contract["methods"] = links
        exact = [link for link in links if link["evidence"] == "contract_label"]
        contract["mapping"] = (
            "flow_review"
            if contract["steps"]
            else "label_unique"
            if len(exact) == 1
            else "label_ambiguous"
            if exact
            else "url_candidate"
            if links
            else "unmatched"
        )
    # A shared label is not sufficient evidence for choosing a Python method.
    ambiguous = {c["id"] for c in contracts if c["mapping"] == "label_ambiguous"}
    for method in methods:
        if any(link["contract"] in ambiguous for link in method["contracts"]):
            method["review_reasons"].append("ambiguous_contract_label")
            method["automation"] = "manual_review"


def build_inventory(root: Path) -> Record:
    root = root.resolve()
    manifest_path = root / "Cargo.toml"
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    domains = set(manifest["features"]["full"])
    contracts, inputs = read_contracts(root)
    paths = sorted((root / "src").rglob("*.rs"))
    if not paths:
        raise ValueError("No Rust source files found")
    for path in paths:
        inside(root, path)
    files = [extract_file(path, root, domains) for path in paths]
    methods = [m for f in files for m in f["methods"]]
    types = [t for f in files for t in f["types"]]
    associate(methods, contracts, files)
    # Include every response file in provenance, even if no case references it.
    responses = sorted((root / "tests/contracts").glob("**/responses/*.json"))
    input_hashes = {}
    for path in sorted(set([manifest_path, *paths, *inputs, *responses])):
        inside(root, path)
        input_hashes[path.relative_to(root).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    digest = hashlib.sha256(json.dumps(input_hashes, sort_keys=True).encode()).hexdigest()
    try:
        revision = git(root, "rev-parse", "HEAD")
        dirty = bool(git(root, "status", "--porcelain", "--untracked-files=no"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        revision, dirty = None, None
    summary = {
        "rust_files": len(paths),
        "domains": len(domains),
        "contracts": len(contracts),
        "response_files": len(responses),
        "public_async_declarations": len(methods),
        "type_declarations": len(types),
        "contract_mapping": dict(sorted(Counter(c["mapping"] for c in contracts).items())),
        "automation": dict(sorted(Counter(m["automation"] for m in methods).items())),
        "review_reasons": dict(
            sorted(Counter(r for m in methods for r in m["review_reasons"]).items())
        ),
    }
    return {
        "schema_version": 1,
        "baseline": {
            "repository": manifest["package"].get("repository"),
            "commit": revision,
            "tracked_dirty": dirty,
            "input_sha256": digest,
            "inputs": input_hashes,
        },
        "limitations": [
            "Static declarations; compiler visibility and cfg selection are not evaluated.",
            "Macros are recorded but not expanded; const/import resolution is candidate evidence.",
            "Parameter expressions and Rust types are preserved, not translated or validated.",
            "request_shell_candidate does not mean fully auto-migratable or implemented.",
            "Contract fixtures are historical evidence; no live requests were made.",
        ],
        "summary": summary,
        "contracts": contracts,
        "methods": methods,
        "types": types,
        "opaque_macros": [m for f in files for m in f["macros"]],
    }


def cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(data: Record) -> str:
    summary = data["summary"]
    lines = [
        "# 第一波迁移覆盖报告",
        "",
        "由 `tools.migration` 生成；不要手动编辑。",
        "",
        f"源提交：`{data['baseline']['commit']}`。输入摘要：`{data['baseline']['input_sha256']}`。",
        "",
        "## 统计",
        "",
        "| 指标 | 数量 |",
        "| --- | --- |",
    ]
    for key, value in summary.items():
        if isinstance(value, int):
            lines.append(f"| {key} | {value} |")
    lines.extend(["", "## 契约关联", "", "| 分类 | 数量 |", "| --- | --- |"])
    for key, value in summary["contract_mapping"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 自动化边界",
            "",
            f"请求壳模板候选：{summary['automation'].get('request_shell_candidate', 0)}。"
            "仍需验证参数辅助函数、类型与认证；不是可直接发布的接口。",
            "其余声明进入人工复核，可按重复原因批量处理。",
            "",
            "| 复核原因（可重叠） | 声明数 |",
            "| --- | --- |",
        ]
    )
    for key, value in summary["review_reasons"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        ["", "## 各领域", "", "| 领域 | 异步声明 | 契约 | 模板候选 |", "| --- | --- | --- | --- |"]
    )
    for domain in sorted(
        {m["domain"] for m in data["methods"]} | {c["domain"] for c in data["contracts"]}
    ):
        methods = [m for m in data["methods"] if m["domain"] == domain]
        lines.append(
            f"| {domain} | {len(methods)} | "
            f"{sum(c['domain'] == domain for c in data['contracts'])} | "
            f"{sum(m['automation'] == 'request_shell_candidate' for m in methods)} |"
        )
    lines.extend(
        [
            "",
            "## 契约 → 源码",
            "",
            "| 契约 | 风险 | 关联状态 | 源码声明 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for contract in data["contracts"]:
        ids = "; ".join(link["method"] for link in contract["methods"]) or "—"
        lines.append(
            f"| {cell(contract['id'])} | {contract['risk']} | {contract['mapping']} | {cell(ids)} |"
        )
    lines.extend(
        [
            "",
            "## 无契约匹配的公开异步声明",
            "",
            "包含旧方法和辅助方法；不把这些数量直接等同于缺失端点数。",
            "",
            "| 声明 | 请求 / 返回处理 |",
            "| --- | --- |",
        ]
    )
    for method in data["methods"]:
        if not method["contracts"]:
            lines.append(f"| {cell(method['id'])} | {cell(', '.join(method['review_reasons']))} |")
    lines.extend(["", "## 局限", "", *[f"- {item}" for item in data["limitations"]], ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if output.is_relative_to(source):
        parser.error("Output must be outside the source repository")
    try:
        data = build_inventory(source)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Inventory failed: {error}\n")
    output.mkdir(parents=True, exist_ok=True)
    (output / "inventory.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "coverage.md").write_text(render_report(data), encoding="utf-8")
    print(json.dumps(data["summary"], ensure_ascii=False, indent=2))
