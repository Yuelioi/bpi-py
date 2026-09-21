from __future__ import annotations

from enum import IntEnum, StrEnum

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


class SearchType(StrEnum):
    VIDEO = "video"
    MEDIA_BANGUMI = "media_bangumi"
    MEDIA_FT = "media_ft"
    LIVE = "live"
    LIVE_ROOM = "live_room"
    LIVE_USER = "live_user"
    ARTICLE = "article"
    BILI_USER = "bili_user"


class SearchOrder(StrEnum):
    TOTAL_RANK = "totalrank"
    CLICK = "click"
    PUB_DATE = "pubdate"
    DM = "dm"
    STOW = "stow"
    SCORES = "scores"
    ATTENTION = "attention"
    ONLINE = "online"
    LIVE_TIME = "live_time"
    DEFAULT = "0"
    FANS = "fans"
    LEVEL = "level"


class OrderSort(IntEnum):
    DESCENDING = 0
    ASCENDING = 1


class UserType(IntEnum):
    ALL = 0
    UP = 1
    NORMAL = 2
    VERIFIED = 3


class Duration(IntEnum):
    ALL = 0
    UNDER_10 = 1
    FROM_10_TO_30 = 2
    FROM_30_TO_60 = 3
    OVER_60 = 4


class CategoryId(IntEnum):
    ALL = 0
    ANIMATION = 2
    GAME = 1
    MOVIE = 28
    LIFE = 3
    INTEREST = 29
    LIGHT_NOVEL = 16
    TECHNOLOGY = 17
    HUAYOU = 1
    PHOTOGRAPHY = 2


def _text(value: str, name: str, message: str) -> str:
    if not isinstance(value, str):
        raise InvalidParameterError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise InvalidParameterError(message)
    return value


def _enum(value: object, kind: type[StrEnum] | type[IntEnum], name: str) -> str:
    if not isinstance(value, kind):
        raise InvalidParameterError(f"{name} has an unsupported value")
    return str(value.value)


def _base(search_type: SearchType, keyword: str, page: int) -> dict[str, str]:
    return {
        "search_type": search_type.value,
        "keyword": _text(keyword, "keyword", "search keyword cannot be blank"),
        "page": integer(page, "page", 1),
    }


def article_params(
    keyword: str,
    order: SearchOrder,
    category_id: CategoryId,
    page: int,
) -> dict[str, str]:
    params = _base(SearchType.ARTICLE, keyword, page)
    params["order"] = _enum(order, SearchOrder, "order")
    params["category_id"] = _enum(category_id, CategoryId, "category_id")
    return params


def bangumi_params(keyword: str, page: int) -> dict[str, str]:
    return _base(SearchType.MEDIA_BANGUMI, keyword, page)


def bili_user_params(
    keyword: str,
    order_sort: OrderSort,
    user_type: UserType,
    page: int,
) -> dict[str, str]:
    params = _base(SearchType.BILI_USER, keyword, page)
    params["order_sort"] = _enum(order_sort, OrderSort, "order_sort")
    params["user_type"] = _enum(user_type, UserType, "user_type")
    return params


def live_params(keyword: str, page: int) -> dict[str, str]:
    return _base(SearchType.LIVE, keyword, page)


def live_room_params(keyword: str, order: SearchOrder, page: int) -> dict[str, str]:
    params = _base(SearchType.LIVE_ROOM, keyword, page)
    params["order"] = _enum(order, SearchOrder, "order")
    return params


def live_user_params(
    keyword: str,
    order_sort: OrderSort,
    user_type: UserType,
    page: int,
) -> dict[str, str]:
    params = _base(SearchType.LIVE_USER, keyword, page)
    params["order_sort"] = _enum(order_sort, OrderSort, "order_sort")
    params["user_type"] = _enum(user_type, UserType, "user_type")
    return params


def movie_params(keyword: str, page: int) -> dict[str, str]:
    return _base(SearchType.MEDIA_FT, keyword, page)


def video_params(
    keyword: str,
    order: SearchOrder,
    duration: Duration,
    tid: int,
    page: int,
) -> dict[str, str]:
    params = _base(SearchType.VIDEO, keyword, page)
    params["order"] = _enum(order, SearchOrder, "order")
    params["duration"] = _enum(duration, Duration, "duration")
    params["tids"] = integer(tid, "tid", 0)
    return params


def suggest_params(term: str) -> dict[str, str]:
    return {"term": _text(term, "term", "search suggestion term cannot be blank")}
