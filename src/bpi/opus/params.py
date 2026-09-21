from __future__ import annotations

from enum import StrEnum

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


class OpusSpaceFeedKind(StrEnum):
    ALL = "all"
    ARTICLE = "article"
    DYNAMIC = "dynamic"


def space_feed_query(
    mid: int,
    page: int,
    offset: str | None,
    kind: OpusSpaceFeedKind | str,
) -> dict[str, str]:
    if type(page) is not int or page < 0:
        raise InvalidParameterError("page must be an integer >= 0")
    if isinstance(kind, OpusSpaceFeedKind):
        kind_value = kind.value
    elif isinstance(kind, str):
        try:
            kind_value = OpusSpaceFeedKind(kind).value
        except ValueError:
            raise InvalidParameterError("kind has an unsupported value") from None
    else:
        raise InvalidParameterError("kind has an unsupported value")
    params = {
        "host_mid": integer(mid, "mid"),
        "page": str(page),
        "type": kind_value,
        "web_location": "333.1387",
    }
    if offset is not None:
        if not isinstance(offset, str) or not offset.strip():
            raise InvalidParameterError("offset cannot be blank")
        params["offset"] = offset
    return params
