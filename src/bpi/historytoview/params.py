from __future__ import annotations

from enum import StrEnum

from bpi.errors import InvalidParameterError


class HistoryBusiness(StrEnum):
    ARCHIVE = "archive"
    PGC = "pgc"
    LIVE = "live"
    ARTICLE_LIST = "article-list"
    ARTICLE = "article"


class HistoryListType(StrEnum):
    ALL = "all"
    ARCHIVE = "archive"
    LIVE = "live"
    ARTICLE = "article"


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise InvalidParameterError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise InvalidParameterError(f"{name} cannot be blank")
    return value


def _uint(value: int, name: str, bits: int, minimum: int = 0) -> str:
    if type(value) is not int or value < minimum or value > (1 << bits) - 1:
        raise InvalidParameterError(f"{name} must be an integer in range")
    return str(value)


def _filter_value(value: HistoryBusiness | HistoryListType | str, name: str) -> str:
    if isinstance(value, (HistoryBusiness, HistoryListType)):
        return value.value
    return _nonblank(value, name)


def history_list_query(
    max_id: int | None,
    business: HistoryBusiness | str | None,
    view_at: int | None,
    list_type: HistoryListType | str | None,
    page_size: int | None,
) -> dict[str, str]:
    params: dict[str, str] = {}
    if max_id is not None:
        params["max"] = _uint(max_id, "max", 64)
    if business is not None:
        params["business"] = _filter_value(business, "business")
    if view_at is not None:
        params["view_at"] = _uint(view_at, "view_at", 64)
    if list_type is not None:
        params["type"] = _filter_value(list_type, "list_type")
    if page_size is not None:
        params["ps"] = _uint(page_size, "page_size", 32, 1)
    return params


def history_delete_form(kid: str, csrf: str) -> dict[str, str]:
    return {"kid": _nonblank(kid, "kid"), "csrf": csrf}


def history_shadow_form(switch: bool, csrf: str) -> dict[str, str]:
    if type(switch) is not bool:
        raise InvalidParameterError("switch must be a boolean")
    return {"switch": str(switch).lower(), "csrf": csrf}


def toview_add_form(aid: int | None, bvid: str | None, csrf: str) -> dict[str, str]:
    form = {"csrf": csrf}
    if aid is not None:
        form["aid"] = _uint(aid, "aid", 64, 1)
    if bvid is not None:
        form["bvid"] = _nonblank(bvid, "bvid")
    if aid is None and bvid is None:
        raise InvalidParameterError("aid or bvid is required")
    return form


def toview_delete_form(aid: int | None, viewed: bool | None, csrf: str) -> dict[str, str]:
    form = {"csrf": csrf}
    if aid is not None:
        form["aid"] = _uint(aid, "aid", 64, 1)
    if viewed is not None:
        if type(viewed) is not bool:
            raise InvalidParameterError("viewed must be a boolean")
        form["viewed"] = str(viewed).lower()
    if aid is None and viewed is None:
        raise InvalidParameterError("aid or viewed is required")
    return form
