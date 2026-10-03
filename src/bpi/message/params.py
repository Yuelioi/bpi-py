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
    receiver = _uint64(receiver_id, "receiver_id")
    kind = integer(receiver_type, "receiver_type")
    if receiver_type not in (1, 2):
        raise InvalidParameterError("receiver_type must be 1 or 2")
    return receiver, kind


class SessionListType(IntEnum):
    USER_AND_SYSTEM = 1
    UNFOLLOWED = 2
    ALL = 4


def _uint64(value: int, field: str) -> str:
    result = integer(value, field)
    if value > 2**64 - 1:
        raise InvalidParameterError(f"{field} exceeds uint64")
    return result


def _page_size(size: int) -> str:
    result = integer(size, "size")
    if size > 100:
        raise InvalidParameterError("size must be between 1 and 100")
    return result


def sessions_query(
    session_type: int | SessionListType,
    size: int,
    begin_ts: int | None,
    end_ts: int | None,
) -> dict[str, str]:
    kind = int(session_type) if isinstance(session_type, SessionListType) else session_type
    kind_text = integer(kind, "session_type")
    if kind not in (1, 2, 4):
        raise InvalidParameterError("session_type must be 1, 2 or 4")
    query = {
        "session_type": kind_text,
        "sort_rule": "2",
        "size": _page_size(size),
        "mobi_app": "web",
        "group_fold": "0",
        "unfollow_fold": "0",
    }
    if begin_ts is not None:
        query["begin_ts"] = _uint64(begin_ts, "begin_ts")
    if end_ts is not None:
        query["end_ts"] = _uint64(end_ts, "end_ts")
    return query


def session_messages_query(
    talker_id: int, size: int, begin_seqno: int | None, end_seqno: int | None
) -> dict[str, str]:
    query = {
        "talker_id": _uint64(talker_id, "talker_id"),
        "session_type": "1",
        "size": _page_size(size),
        "mobi_app": "web",
    }
    if begin_seqno is not None:
        query["begin_seqno"] = _uint64(begin_seqno, "begin_seqno")
    if end_seqno is not None:
        query["end_seqno"] = _uint64(end_seqno, "end_seqno")
    return query
