from __future__ import annotations

from bpi._core.params import integer, video_id
from bpi.errors import InvalidParameterError


def info_query(sid: int, bvid: str | None) -> dict[str, str]:
    params = {"sid": integer(sid, "sid")}
    if bvid is not None:
        params.update(video_id(None, bvid))
    return params


def list_query(
    platform_filter: str,
    mold: int,
    http_mode: int,
    page: int,
    page_size: int,
) -> dict[str, str]:
    if not isinstance(platform_filter, str) or not platform_filter.strip():
        raise InvalidParameterError("platform_filter cannot be blank")
    return {
        "plat": platform_filter,
        "mold": integer(mold, "mold", minimum=0),
        "http": integer(http_mode, "http_mode", minimum=0),
        "pn": integer(page, "page"),
        "ps": integer(page_size, "page_size"),
    }
