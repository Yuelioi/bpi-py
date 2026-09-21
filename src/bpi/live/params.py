from __future__ import annotations

import base64

from bpi.errors import InvalidParameterError


def positive(name: str, value: int) -> int:
    if type(value) is not int or value <= 0:
        raise InvalidParameterError(f"{name} must be positive")
    return value


def positive_optional(name: str, value: int | None) -> int | None:
    if value is None:
        return None
    return positive(name, value)


def nonblank(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value


def nonblank_optional(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    return nonblank(name, value)


def stream_query(
    cid: int,
    platform: str | None,
    quality: int | None,
    qn: int | None,
) -> dict[str, str]:
    params = {"cid": str(positive("cid", cid))}
    if platform is not None:
        params["platform"] = nonblank("platform", platform)
    if quality is not None:
        params["quality"] = str(positive("quality", quality))
    if qn is not None:
        params["qn"] = str(positive("qn", qn))
    return params


def room_gift_query(
    room_id: int, area_parent_id: int | None, area_id: int | None
) -> dict[str, str]:
    params = {"room_id": str(positive("room_id", room_id)), "platform": "web"}
    area_parent_id = positive_optional("area_parent_id", area_parent_id)
    area_id = positive_optional("area_id", area_id)
    if area_parent_id is not None:
        params["area_parent_id"] = str(area_parent_id)
    if area_id is not None:
        params["area_id"] = str(area_id)
    return params


def optional_page_query(
    page: int | None,
    page_size: int | None,
) -> dict[str, str]:
    params: dict[str, str] = {}
    page = positive_optional("page", page)
    page_size = positive_optional("page_size", page_size)
    if page is not None:
        params["page"] = str(page)
    if page_size is not None:
        params["page_size"] = str(page_size)
    return params


def moderation_referer(room_id: int) -> str:
    return f"https://live.bilibili.com/{positive('room_id', room_id)}"


def heartbeat_query(room_id: int, next_interval: int, platform: str) -> dict[str, str]:
    room_id = positive("room_id", room_id)
    next_interval = positive("next_interval", next_interval)
    platform = nonblank("platform", platform)
    raw = f"{next_interval}|{room_id}|1|0".encode()
    return {"hb": base64.b64encode(raw).decode(), "pf": platform}
