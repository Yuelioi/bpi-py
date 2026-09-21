from __future__ import annotations

from datetime import date

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


def _non_blank(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value.strip()


def _date(value: date, name: str) -> str:
    if type(value) is not date:
        raise InvalidParameterError(f"{name} must be a date")
    return value.strftime("%Y-%m-%d")


def month_up_list_query(up_mid: int) -> dict[str, str]:
    return {"up_mid": integer(up_mid, "up_mid")}


def video_show_query(mid: int, aid: int | None = None, bvid: str | None = None) -> dict[str, str]:
    query = {"mid": integer(mid, "mid")}
    if aid is not None:
        query["aid"] = integer(aid, "aid")
    if bvid is not None:
        query["bvid"] = _non_blank(bvid, "bvid")
    return query


def recharge_list_query(
    page: int,
    page_size: int,
    begin_time: date | None = None,
    end_time: date | None = None,
) -> dict[str, str]:
    query = {
        "customerId": "10026",
        "currentPage": integer(page, "page"),
        "pageSize": integer(page_size, "page_size"),
    }
    if begin_time is not None:
        query["beginTime"] = _date(begin_time, "begin_time")
    if end_time is not None:
        query["endTime"] = _date(end_time, "end_time")
    return query


def rank_recent_query(pn: int | None = None, ps: int | None = None) -> dict[str, str]:
    query: dict[str, str] = {}
    if pn is not None:
        query["pn"] = integer(pn, "pn")
    if ps is not None:
        query["ps"] = integer(ps, "ps")
    return query


def charge_record_query(page: int, charge_type: int) -> dict[str, str]:
    return {
        "page": integer(page, "page"),
        "type": integer(charge_type, "charge_type", minimum=0),
    }


def upower_member_rank_query(
    up_mid: int, pn: int, ps: int, privilege_type: int | None = None
) -> dict[str, str]:
    query = {
        "up_mid": integer(up_mid, "up_mid"),
        "pn": integer(pn, "pn"),
        "ps": integer(ps, "ps"),
    }
    if privilege_type is not None:
        query["privilege_type"] = integer(privilege_type, "privilege_type", minimum=0)
    return query


def remark_list_query(
    pn: int | None = None,
    ps: int | None = None,
    begin: date | None = None,
    end: date | None = None,
) -> dict[str, str]:
    query = rank_recent_query(pn, ps)
    if begin is not None:
        query["begin"] = _date(begin, "begin")
    if end is not None:
        query["end"] = _date(end, "end")
    return query


def remark_detail_query(id: int) -> dict[str, str]:
    return {"id": integer(id, "id")}


def bcoin_quick_pay_form(
    bp_num: int,
    is_bp_remains_prior: bool,
    up_mid: int,
    otype: str,
    oid: int,
    *,
    csrf: str = "",
) -> dict[str, str]:
    if type(bp_num) is not int or not 2 <= bp_num <= 9999:
        raise InvalidParameterError("bp_num must be an integer between 2 and 9999")
    if type(is_bp_remains_prior) is not bool:
        raise InvalidParameterError("is_bp_remains_prior must be a boolean")
    if otype not in ("up", "archive"):
        raise InvalidParameterError("otype must be 'up' or 'archive'")
    return {
        "bp_num": str(bp_num),
        "is_bp_remains_prior": "true" if is_bp_remains_prior else "false",
        "up_mid": integer(up_mid, "up_mid"),
        "otype": otype,
        "oid": integer(oid, "oid"),
        "csrf": csrf,
    }


def message_form(order_id: str, message: str, *, csrf: str = "") -> dict[str, str]:
    return {
        "order_id": _non_blank(order_id, "order_id"),
        "message": _non_blank(message, "message"),
        "csrf": csrf,
    }


def reply_remark_form(id: int, msg: str, *, csrf: str = "") -> dict[str, str]:
    return {
        "id": integer(id, "id"),
        "msg": _non_blank(msg, "msg"),
        "csrf": csrf,
    }
