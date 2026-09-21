from __future__ import annotations

from enum import IntEnum

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


class SingleUnreadType(IntEnum):
    ALL = 0
    FOLLOW = 1
    UNFOLLOW = 2
    BLOCKED = 3


def _non_blank(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidParameterError(f"{field} must be a string")
    result = value.strip()
    if not result:
        raise InvalidParameterError(f"{field} cannot be blank")
    return result


def unread_count_query(build: str, mobi_app: str) -> dict[str, str]:
    return {"build": _non_blank(build, "build"), "mobi_app": _non_blank(mobi_app, "mobi_app")}


def reply_feed_query(
    start_id: int | None,
    start_time: int | None,
    web_location: str,
) -> dict[str, str]:
    if not isinstance(web_location, str):
        raise InvalidParameterError("web_location must be a string")
    params = {"build": "0", "mobi_app": "web", "platform": "web", "web_location": web_location}
    if start_id is not None:
        params["id"] = integer(start_id, "start_id")
    if start_time is not None:
        params["reply_time"] = integer(start_time, "start_time")
    return params


def single_unread_query(
    unread_type: int | SingleUnreadType,
    show_unfollow_list: bool,
    show_dustbin: bool | None,
) -> dict[str, str]:
    raw_type = int(unread_type) if isinstance(unread_type, SingleUnreadType) else unread_type
    value = integer(raw_type, "unread_type", minimum=0)
    if not isinstance(show_unfollow_list, bool):
        raise InvalidParameterError("show_unfollow_list must be a bool")
    if show_dustbin is not None and not isinstance(show_dustbin, bool):
        raise InvalidParameterError("show_dustbin must be a bool or None")
    blocked = int(value) == SingleUnreadType.BLOCKED
    dustbin = blocked if show_dustbin is None else show_dustbin
    return {
        "build": "0",
        "mobi_app": "web",
        "unread_type": value,
        "show_unfollow_list": "1" if show_unfollow_list else "0",
        "show_dustbin": "1" if dustbin else "0",
    }


def receiver_query(receiver_id: int, receiver_type: int) -> tuple[str, str]:
    receiver = integer(receiver_id, "receiver_id")
    kind = integer(receiver_type, "receiver_type")
    if receiver_type not in (1, 2):
        raise InvalidParameterError("receiver_type must be 1 or 2")
    return receiver, kind
