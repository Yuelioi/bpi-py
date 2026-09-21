from __future__ import annotations

import re

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


def _bounded_integer(value: int, name: str, minimum: int, maximum: int) -> str:
    text = integer(value, name, minimum=minimum)
    if value > maximum:
        raise InvalidParameterError(f"{name} must be an integer <= {maximum}")
    return text


def coupons_body(page_num: int, page_size: int) -> dict[str, object]:
    return {
        "pageNum": int(integer(page_num, "page_num")),
        "pageSize": int(_bounded_integer(page_size, "page_size", 1, 100)),
        "notExpired": True,
        "tabType": 1,
        "type": 0,
    }


def platform_form() -> dict[str, str]:
    return {"platform": "android"}


def clock_in_makeup_body(value: str) -> dict[str, object]:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InvalidParameterError("date must use YYYY-MM-DD")
    return {"type": 0, "date": value}


def buy_episode_body(
    ep_id: int,
    buy_method: int,
    coupon_id: int,
    *,
    comic_id: int | None = None,
    auto_pay_gold_status: int | None = None,
    is_presale: int | None = None,
    pay_amount: int | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "epId": int(integer(ep_id, "ep_id")),
        "buyMethod": int(integer(buy_method, "buy_method")),
        "couponId": int(integer(coupon_id, "coupon_id", minimum=0)),
    }
    if comic_id is not None:
        body["comicId"] = int(integer(comic_id, "comic_id"))
    if auto_pay_gold_status is not None:
        body["autoPayGoldStatus"] = int(
            integer(auto_pay_gold_status, "auto_pay_gold_status", minimum=0)
        )
    if is_presale is not None:
        body["isPresale"] = int(integer(is_presale, "is_presale", minimum=0))
    if pay_amount is not None:
        body["payAmount"] = int(integer(pay_amount, "pay_amount", minimum=0))
    return body


def point_exchange_form(product_id: int, product_num: int, point: int) -> dict[str, str]:
    return {
        "product_id": integer(product_id, "product_id"),
        "product_num": integer(product_num, "product_num"),
        "point": integer(point, "point", minimum=0),
    }
