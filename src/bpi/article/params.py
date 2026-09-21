from __future__ import annotations

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


def _non_blank(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value.strip()


def info_query(article_id: int) -> dict[str, str]:
    return {"id": integer(article_id, "id")}


def view_query(article_id: int, gaia_source: str) -> dict[str, str]:
    return {
        "id": integer(article_id, "id"),
        "gaia_source": _non_blank(gaia_source, "gaia_source"),
    }


def cards_query(ids: str, web_location: str) -> dict[str, str]:
    return {
        "ids": _non_blank(ids, "ids"),
        "web_location": _non_blank(web_location, "web_location"),
    }


def like_form(article_id: int, like: bool, csrf: str) -> dict[str, str]:
    if type(like) is not bool:
        raise InvalidParameterError("like must be a boolean")
    return {
        "id": integer(article_id, "id"),
        "type": "1" if like else "2",
        "csrf": csrf,
    }


def coin_form(aid: int, upid: int, multiply: int, csrf: str) -> dict[str, str]:
    if type(multiply) is not int or multiply not in (1, 2):
        raise InvalidParameterError("multiply must be 1 or 2")
    return {
        "aid": integer(aid, "aid"),
        "upid": integer(upid, "upid"),
        "multiply": str(multiply),
        "avtype": "2",
        "csrf": csrf,
    }


def favorite_form(article_id: int, csrf: str) -> dict[str, str]:
    return {"id": integer(article_id, "id"), "csrf": csrf}
