from __future__ import annotations

from enum import IntEnum

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


class CommentSort(IntEnum):
    TIME = 0
    LIKE = 1
    REPLIES = 2


class CommentType(IntEnum):
    VIDEO = 1
    ARTICLE = 12
    DYNAMIC = 17


class ReportReason(IntEnum):
    OTHER = 0
    AD = 1
    PORN = 2
    SPAM = 3
    FLAME = 4
    SPOILER = 5
    POLITICS = 6
    ABUSE = 7
    IRRELEVANT = 8
    ILLEGAL = 9
    VULGAR = 10
    PHISHING = 11
    SCAM = 12
    RUMOR = 13
    INCITEMENT = 14
    PRIVACY = 15
    FLOOR_SNATCHING = 16
    HARMFUL_TO_YOUTH = 17


def _positive(value: int, name: str) -> str:
    return integer(value, name)


def _non_blank(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value.strip()


def _enum_value(value: IntEnum | int, enum: type[IntEnum], name: str) -> str:
    if isinstance(value, bool):
        raise InvalidParameterError(f"{name} has an invalid value")
    try:
        return str(enum(value).value)
    except (TypeError, ValueError):
        raise InvalidParameterError(f"{name} has an invalid value") from None


def target_query(comment_type: int, oid: int) -> dict[str, str]:
    return {"type": _positive(comment_type, "type"), "oid": _positive(oid, "oid")}


def list_query(
    comment_type: int,
    oid: int,
    *,
    page: int | None = None,
    page_size: int | None = None,
    sort: CommentSort | int | None = None,
    nohot: bool | None = None,
) -> dict[str, str]:
    params = target_query(comment_type, oid)
    if page is not None:
        params["pn"] = _positive(page, "pn")
    if page_size is not None:
        page_size_text = _positive(page_size, "ps")
        if page_size > 20:
            raise InvalidParameterError("ps must be less than or equal to 20")
        params["ps"] = page_size_text
    if sort is not None:
        params["sort"] = _enum_value(sort, CommentSort, "sort")
    if nohot is not None:
        if type(nohot) is not bool:
            raise InvalidParameterError("nohot must be a boolean")
        params["nohot"] = "1" if nohot else "0"
    return params


def replies_query(
    comment_type: int,
    oid: int,
    root: int,
    *,
    page: int | None = None,
    page_size: int | None = None,
) -> dict[str, str]:
    params = target_query(comment_type, oid)
    params["root"] = _positive(root, "root")
    if page is not None:
        params["pn"] = _positive(page, "pn")
    if page_size is not None:
        params["ps"] = _positive(page_size, "ps")
    return params


def add_form(
    comment_type: CommentType | int,
    oid: int,
    message: str,
    *,
    root: int | None = None,
    parent: int | None = None,
    csrf: str = "",
) -> dict[str, str]:
    form = {
        "type": _enum_value(comment_type, CommentType, "type"),
        "oid": _positive(oid, "oid"),
        "message": _non_blank(message, "message"),
        "plat": "1",
        "csrf": csrf,
    }
    if root is not None:
        form["root"] = _positive(root, "root")
    if parent is not None:
        form["parent"] = _positive(parent, "parent")
    return form


def action_form(
    comment_type: CommentType | int,
    oid: int,
    rpid: int,
    action: int,
    *,
    csrf: str = "",
) -> dict[str, str]:
    if type(action) is not int or action not in (0, 1):
        raise InvalidParameterError("action must be 0 or 1")
    return {
        "type": _enum_value(comment_type, CommentType, "type"),
        "oid": _positive(oid, "oid"),
        "rpid": _positive(rpid, "rpid"),
        "action": str(action),
        "csrf": csrf,
    }


def delete_form(
    comment_type: CommentType | int, oid: int, rpid: int, *, csrf: str = ""
) -> dict[str, str]:
    return {
        "type": _enum_value(comment_type, CommentType, "type"),
        "oid": _positive(oid, "oid"),
        "rpid": _positive(rpid, "rpid"),
        "csrf": csrf,
    }


def report_form(
    comment_type: CommentType | int,
    oid: int,
    rpid: int,
    reason: ReportReason | int,
    *,
    content: str | None = None,
    csrf: str = "",
) -> dict[str, str]:
    form = {
        **delete_form(comment_type, oid, rpid, csrf=csrf),
        "reason": _enum_value(reason, ReportReason, "reason"),
    }
    if content is not None:
        form["content"] = _non_blank(content, "content")
    return form
