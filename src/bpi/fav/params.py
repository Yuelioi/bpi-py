from __future__ import annotations

from bpi._core.params import integer
from bpi.errors import InvalidParameterError


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise InvalidParameterError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise InvalidParameterError(f"{name} cannot be blank")
    return value


def _uint(value: int, name: str, bits: int, minimum: int = 0) -> str:
    if type(value) is not int or value < minimum or value > (1 << bits) - 1:
        raise InvalidParameterError(f"{name} must be an integer in range")
    return str(value)


def folder_info_query(media_id: int) -> dict[str, str]:
    return {"media_id": integer(media_id, "media_id")}


def created_list_query(
    up_mid: int,
    type_id: int | None,
    resource_id: int | None,
    web_location: str,
) -> dict[str, str]:
    params = {"up_mid": integer(up_mid, "up_mid")}
    if type_id is not None:
        params["type"] = _uint(type_id, "type_id", 8)
    if resource_id is not None:
        params["rid"] = integer(resource_id, "resource_id")
    params["web_location"] = _nonblank(web_location, "web_location")
    return params


def collected_list_query(
    up_mid: int, page: int, page_size: int, platform: str
) -> dict[str, str]:
    return {
        "up_mid": integer(up_mid, "up_mid"),
        "pn": integer(page, "page"),
        "ps": integer(page_size, "page_size"),
        "platform": _nonblank(platform, "platform"),
    }


def resource_infos_query(resources: str, platform: str) -> dict[str, str]:
    return {
        "resources": _nonblank(resources, "resources"),
        "platform": _nonblank(platform, "platform"),
    }


def resource_ids_query(media_id: int, platform: str) -> dict[str, str]:
    return {
        "media_id": integer(media_id, "media_id"),
        "platform": _nonblank(platform, "platform"),
    }


def list_detail_query(
    media_id: int,
    tid: int | None,
    keyword: str | None,
    order: str | None,
    content_type: int | None,
    page_size: int,
    page: int | None,
) -> dict[str, str]:
    params = {
        "media_id": integer(media_id, "media_id"),
        "ps": integer(page_size, "page_size"),
        "platform": "web",
    }
    if tid is not None:
        params["tid"] = _uint(tid, "tid", 32)
    if keyword is not None:
        params["keyword"] = _nonblank(keyword, "keyword")
    if order is not None:
        params["order"] = _nonblank(order, "order")
    if content_type is not None:
        params["type"] = _uint(content_type, "content_type", 8)
    if page is not None:
        params["pn"] = integer(page, "page")
    return params


def _optional_text(form: dict[str, str], name: str, value: str | None) -> None:
    if value is not None:
        form[name] = _nonblank(value, name)


def folder_form(
    *,
    csrf: str,
    title: str,
    media_id: int | None = None,
    intro: str | None = None,
    privacy: int | None = None,
    cover: str | None = None,
) -> dict[str, str]:
    form: dict[str, str] = {}
    if media_id is not None:
        form["media_id"] = integer(media_id, "media_id")
    form["title"] = _nonblank(title, "title")
    form["csrf"] = csrf
    _optional_text(form, "intro", intro)
    if privacy is not None:
        if type(privacy) is not int or privacy not in (0, 1):
            raise InvalidParameterError("privacy must be 0 or 1")
        form["privacy"] = str(privacy)
    _optional_text(form, "cover", cover)
    return form


def delete_folders_form(media_ids: list[int], csrf: str) -> dict[str, str]:
    if not isinstance(media_ids, list) or not media_ids:
        raise InvalidParameterError("media_ids must be a non-empty list")
    values = [integer(item, "media_ids") for item in media_ids]
    return {"media_ids": ",".join(values), "csrf": csrf}


def transfer_form(
    src_media_id: int,
    tar_media_id: int,
    mid: int,
    resources: str,
    csrf: str,
) -> dict[str, str]:
    return {
        "src_media_id": integer(src_media_id, "src_media_id"),
        "tar_media_id": integer(tar_media_id, "tar_media_id"),
        "mid": integer(mid, "mid"),
        "resources": _nonblank(resources, "resources"),
        "platform": "web",
        "csrf": csrf,
    }


def delete_resources_form(media_id: int, resources: str, csrf: str) -> dict[str, str]:
    return {
        "media_id": integer(media_id, "media_id"),
        "resources": _nonblank(resources, "resources"),
        "platform": "web",
        "csrf": csrf,
    }


def clean_resources_form(media_id: int, csrf: str) -> dict[str, str]:
    return {"media_id": integer(media_id, "media_id"), "csrf": csrf}
