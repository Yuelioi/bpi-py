from __future__ import annotations

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


def _non_blank(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value.strip()


def notice_query(mid: int, buvid: str | None = None) -> dict[str, str]:
    query = {"mid": integer(mid, "mid")}
    if buvid is not None:
        query["buvid"] = _non_blank(buvid, "buvid")
    return query


def log_query(jsonp: str = "jsonp", web_location: str = "333.33") -> dict[str, str]:
    return {
        "jsonp": _non_blank(jsonp, "jsonp"),
        "web_location": _non_blank(web_location, "web_location"),
    }


def qr_poll_query(qrcode_key: str) -> dict[str, str]:
    return {"qrcode_key": _non_blank(qrcode_key, "qrcode_key")}


def logout_form(csrf: str, gourl: str = "javascript:history.go(-1)") -> dict[str, str]:
    return {"biliCSRF": csrf, "gourl": gourl}


def sms_code_form(
    cid: int,
    tel: str,
    token: str,
    challenge: str,
    validate: str,
    seccode: str,
    *,
    source: str = "main_web",
) -> dict[str, str]:
    return {
        "cid": integer(cid, "cid"),
        "tel": _non_blank(tel, "tel"),
        "source": _non_blank(source, "source"),
        "token": _non_blank(token, "token"),
        "challenge": _non_blank(challenge, "challenge"),
        "validate": _non_blank(validate, "validate"),
        "seccode": _non_blank(seccode, "seccode"),
    }


def sms_login_form(cid: int, tel: int, captcha_key: str, code: str) -> dict[str, str]:
    return {
        "cid": integer(cid, "cid"),
        "tel": integer(tel, "tel"),
        "code": _non_blank(code, "code"),
        "source": "main_web",
        "captcha_key": _non_blank(captcha_key, "captcha_key"),
        "go_url": "https://www.bilibili.com",
        "keep": "true",
    }


def user_sign_form(user_sign: str, csrf: str) -> dict[str, str]:
    if not isinstance(user_sign, str):
        raise InvalidParameterError("user_sign must be a string")
    if len(user_sign.encode("utf-8")) > 70:
        raise InvalidParameterError("user_sign length cannot exceed 70 bytes")
    return {"user_sign": user_sign, "csrf": csrf}
