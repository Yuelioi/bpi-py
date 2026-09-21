from __future__ import annotations

import re
from collections.abc import Iterable

from bpi._core.params import integer, video_id
from bpi.errors import InvalidParameterError


def _uint(value: int, name: str, maximum: int) -> str:
    if type(value) is not int or value < 0 or value > maximum:
        raise InvalidParameterError(f"{name} must be an integer between 0 and {maximum}")
    return str(value)


def _positive(value: int, name: str) -> str:
    return integer(value, name)


def _nonzero_u8(value: int, name: str) -> str:
    text = _uint(value, name, 255)
    if value == 0:
        raise InvalidParameterError(f"{name} must be non-zero")
    return text


def _month(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}", value):
        raise InvalidParameterError("month must use YYYY-MM format")
    month = int(value[5:7])
    if not 1 <= month <= 12:
        raise InvalidParameterError("month must be between 01 and 12")
    return value


def _date(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InvalidParameterError("date must use YYYY-MM-DD format")
    month = int(value[5:7])
    day = int(value[8:10])
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        raise InvalidParameterError("date month/day is out of range")
    return value


def _non_blank(value: str, name: str, *, trim: bool) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value.strip() if trim else value


def _ids(values: Iterable[int], name: str) -> str:
    ids = list(values)
    if not ids:
        raise InvalidParameterError(f"{name} must be non-empty")
    return ",".join(_positive(value, name) for value in ids)


def history_dates_query(oid: int, month: str, *, danmaku_type: int = 1) -> dict[str, str]:
    return {
        "type": _nonzero_u8(danmaku_type, "type"),
        "oid": _positive(oid, "oid"),
        "month": _month(month),
    }


def snapshot_query(*, aid: int | None = None, bvid: str | None = None) -> dict[str, str]:
    target = video_id(aid, bvid)
    return {"aid": next(iter(target.values()))}


def thumbup_stats_query(oid: int, ids: Iterable[int]) -> dict[str, str]:
    return {"oid": _positive(oid, "oid"), "ids": _ids(ids, "ids")}


def adv_state_query(cid: int) -> dict[str, str]:
    return {"cid": _positive(cid, "cid"), "mode": "sp"}


def segment_query(
    danmaku_type: int,
    oid: int,
    segment_index: int,
    *,
    pid: int | None = None,
    pull_mode: int | None = None,
    ps: int | None = None,
    pe: int | None = None,
) -> dict[str, str]:
    params = {
        "type": _nonzero_u8(danmaku_type, "type"),
        "oid": _positive(oid, "oid"),
        "segment_index": _uint(segment_index, "segment_index", 2**32 - 1),
    }
    if segment_index == 0:
        raise InvalidParameterError("segment_index must be non-zero")
    if pid is not None:
        params["pid"] = _positive(pid, "pid")
    if pull_mode is not None:
        params["pull_mode"] = _uint(pull_mode, "pull_mode", 2**32 - 1)
    if (ps is None) != (pe is None):
        raise InvalidParameterError("ps and pe must be provided together")
    if ps is not None and pe is not None:
        ps_text = _uint(ps, "ps", 2**32 - 1)
        pe_text = _uint(pe, "pe", 2**32 - 1)
        if pe < ps:
            raise InvalidParameterError("pe must be greater than or equal to ps")
        params["ps"] = ps_text
        params["pe"] = pe_text
    return params


def web_view_query(
    danmaku_type: int, oid: int, *, pid: int | None = None
) -> dict[str, str]:
    params = {
        "type": _nonzero_u8(danmaku_type, "type"),
        "oid": _positive(oid, "oid"),
    }
    if pid is not None:
        params["pid"] = _positive(pid, "pid")
    return params


def history_bytes_query(danmaku_type: int, oid: int, date: str) -> dict[str, str]:
    return {
        "type": _nonzero_u8(danmaku_type, "type"),
        "oid": _positive(oid, "oid"),
        "date": _date(date),
    }


def xml_list_query(cid: int) -> dict[str, str]:
    return {"oid": _positive(cid, "cid")}


def send_form(
    oid: int,
    msg: str,
    *,
    aid: int | None = None,
    bvid: str | None = None,
    mode: int = 1,
    danmaku_type: int = 1,
    progress: int = 1878,
    color: int = 16_777_215,
    font_size: int = 25,
    pool: int = 0,
    csrf: str = "",
) -> dict[str, str]:
    form = {
        "type": _uint(danmaku_type, "type", 255),
        "oid": _positive(oid, "oid"),
        "msg": _non_blank(msg, "msg", trim=False),
        "mode": _uint(mode, "mode", 255),
        "fontsize": _uint(font_size, "font_size", 255),
        "color": _uint(color, "color", 2**32 - 1),
        "pool": _uint(pool, "pool", 255),
        "progress": _uint(progress, "progress", 2**32 - 1),
        "rnd": "2",
        "plat": "1",
        "csrf": csrf,
        "checkbox_type": "0",
        "colorful": "",
        "gaiasource": "main_web",
        "polaris_app_id": "100",
        "polaris_platform": "5",
        "spmid": "333.788.0.0",
        "from_spmid": "333.788.0.0",
    }
    if aid is not None:
        form["avid"] = _positive(aid, "aid")
    if bvid is not None:
        form["bvid"] = video_id(None, bvid)["bvid"]
    return form


def recall_form(cid: int, dmid: int, *, csrf: str = "") -> dict[str, str]:
    return {
        "cid": _positive(cid, "cid"),
        "dmid": _positive(dmid, "dmid"),
        "type": "1",
        "csrf": csrf,
    }


def buy_adv_form(cid: int, *, csrf: str = "") -> dict[str, str]:
    return {"cid": _positive(cid, "cid"), "mode": "sp", "csrf": csrf}


def thumbup_form(oid: int, dmid: int, op: int, *, csrf: str = "") -> dict[str, str]:
    if type(op) is not int or op not in (1, 2):
        raise InvalidParameterError("op must be 1 or 2")
    return {
        "oid": _positive(oid, "oid"),
        "dmid": _positive(dmid, "dmid"),
        "op": str(op),
        "csrf": csrf,
        "platform": "web_player",
    }


def report_form(
    cid: int, dmid: int, reason: int, *, content: str | None = None, csrf: str = ""
) -> dict[str, str]:
    form = {
        "cid": _positive(cid, "cid"),
        "dmid": _positive(dmid, "dmid"),
        "reason": _uint(reason, "reason", 255),
        "csrf": csrf,
    }
    if content is not None:
        form["content"] = _non_blank(content, "content", trim=True)
    return form


def edit_state_form(
    oid: int, dmids: Iterable[int], state: int, *, csrf: str = ""
) -> dict[str, str]:
    return {
        "type": "1",
        "oid": _positive(oid, "oid"),
        "dmids": _ids(dmids, "dmids"),
        "state": _uint(state, "state", 255),
        "csrf": csrf,
    }


def edit_pool_form(
    oid: int, dmids: Iterable[int], pool: int, *, csrf: str = ""
) -> dict[str, str]:
    return {
        "type": "1",
        "oid": _positive(oid, "oid"),
        "dmids": _ids(dmids, "dmids"),
        "pool": _uint(pool, "pool", 255),
        "csrf": csrf,
    }
