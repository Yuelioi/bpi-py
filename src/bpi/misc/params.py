from __future__ import annotations

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


def _non_blank(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value.strip()


def b23_short_link_form(
    aid: int,
    *,
    platform: str = "unix",
    share_channel: str = "COPY",
    share_id: str = "main.ugc-video-detail.0.0.pv",
    share_mode: int = 4,
    buvid: str = "qwq",
    build: int = 6_114_514,
) -> dict[str, str]:
    return {
        "platform": _non_blank(platform, "platform"),
        "share_channel": _non_blank(share_channel, "share_channel"),
        "share_id": _non_blank(share_id, "share_id"),
        "share_mode": integer(share_mode, "share_mode", minimum=0),
        "oid": integer(aid, "aid"),
        "buvid": _non_blank(buvid, "buvid"),
        "build": integer(build, "build", minimum=0),
    }
