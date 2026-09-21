from __future__ import annotations

import json

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


def _non_blank(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value


def pagination(page: int, page_size: int) -> dict[str, str]:
    return {
        "pn": integer(page, "pn"),
        "ps": integer(page_size, "ps"),
    }


def is_forbid_query(aid: int) -> dict[str, str]:
    return {"aid": integer(aid, "aid")}


def private_info_query(aid: int, note_id: int) -> dict[str, str]:
    return {
        "oid": integer(aid, "aid"),
        "oid_type": "0",
        "note_id": integer(note_id, "note_id"),
    }


def public_info_query(cvid: int) -> dict[str, str]:
    return {"cvid": integer(cvid, "cvid")}


def archive_query(aid: int) -> dict[str, str]:
    return {"oid": integer(aid, "aid"), "oid_type": "0"}


def public_archive_query(aid: int, page: int, page_size: int) -> dict[str, str]:
    return {**archive_query(aid), **pagination(page, page_size)}


def add_form(
    aid: int,
    title: str,
    summary: str,
    content: str,
    *,
    note_id: str | None = None,
    tags: str | None = None,
    publish: bool | None = None,
    auto_comment: bool | None = None,
    csrf: str = "",
) -> dict[str, str]:
    title = _non_blank(title, "title")
    summary = _non_blank(summary, "summary")
    content = _non_blank(content, "content")
    form = {
        "oid": integer(aid, "aid"),
        "oid_type": "0",
        "title": title,
        "summary": summary,
        "content": json.dumps([{"insert": content}], ensure_ascii=False, separators=(",", ":")),
        "cls": "1",
        "from": "save",
        "platform": "web",
        "csrf": csrf,
    }
    if tags is not None:
        form["tags"] = _non_blank(tags, "tags")
    if note_id is not None:
        form["note_id"] = _non_blank(note_id, "note_id")
    for name, value in (("publish", publish), ("auto_comment", auto_comment)):
        if value is not None:
            if type(value) is not bool:
                raise InvalidParameterError(f"{name} must be a boolean")
            form[name] = "1" if value else "0"
    return form


def delete_form(aid: int, note_id: str | None = None, *, csrf: str = "") -> dict[str, str]:
    form = {"oid": integer(aid, "aid"), "csrf": csrf}
    if note_id is not None:
        form["note_id"] = _non_blank(note_id, "note_id")
    return form
