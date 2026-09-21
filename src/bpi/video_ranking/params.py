from __future__ import annotations

from enum import StrEnum

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


class VideoRankingType(StrEnum):
    ALL = "all"
    ROOKIE = "rookie"
    ORIGIN = "origin"


class VideoNewListRankOrder(StrEnum):
    CLICK = "click"
    SCORES = "scores"
    PUBDATE = "pubdate"


def _optional_positive(value: int | None, name: str) -> str | None:
    return None if value is None else integer(value, name)


def _enum_value(value: StrEnum | str, kind: type[StrEnum], name: str) -> str:
    if isinstance(value, kind):
        return value.value
    if isinstance(value, str):
        try:
            return kind(value).value
        except ValueError:
            pass
    raise InvalidParameterError(f"{name} has an unsupported value")


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value


def popular_list_query(page: int | None, page_size: int | None) -> dict[str, str]:
    params: dict[str, str] = {}
    if (value := _optional_positive(page, "page")) is not None:
        params["pn"] = value
    if (value := _optional_positive(page_size, "page_size")) is not None:
        params["ps"] = value
    return params


def ranking_list_query(
    rid: int | None, ranking_type: VideoRankingType | str | None
) -> dict[str, str]:
    params: dict[str, str] = {}
    if (value := _optional_positive(rid, "rid")) is not None:
        params["rid"] = value
    if ranking_type is not None:
        params["type"] = _enum_value(ranking_type, VideoRankingType, "ranking_type")
    return params


def region_query(rid: int, page: int | None, page_size: int | None) -> dict[str, str]:
    params = {"rid": integer(rid, "rid")}
    params.update(popular_list_query(page, page_size))
    return params


def region_tag_query(
    rid: int, tag_id: int, page: int | None, page_size: int | None
) -> dict[str, str]:
    params = region_query(rid, page, page_size)
    params["tag_id"] = integer(tag_id, "tag_id")
    return params


def region_newlist_query(
    rid: int,
    page: int | None,
    page_size: int | None,
    typ: int | None,
) -> dict[str, str]:
    params = region_query(rid, page, page_size)
    if (value := _optional_positive(typ, "type")) is not None:
        params["type"] = value
    return params


def region_newlist_rank_query(
    cate_id: int,
    page_size: int,
    time_from: str,
    time_to: str,
    order: VideoNewListRankOrder | str | None,
    page: int | None,
) -> dict[str, str]:
    params = {
        "search_type": "video",
        "view_type": "hot_rank",
        "cate_id": integer(cate_id, "cate_id"),
        "pagesize": integer(page_size, "page_size"),
        "time_from": _nonblank(time_from, "time_from"),
        "time_to": _nonblank(time_to, "time_to"),
    }
    if order is not None:
        params["order"] = _enum_value(order, VideoNewListRankOrder, "order")
    if (value := _optional_positive(page, "page")) is not None:
        params["page"] = value
    return params
