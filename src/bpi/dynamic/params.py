from __future__ import annotations

from collections.abc import Sequence

from bpi._core.params import integer
from bpi.errors import InvalidParameterError

from .models import DynamicContentItem, DynamicCreatePic, DynamicTopic

DEFAULT_ALL_FEATURES = (
    "itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote,decorationCard,"
    "onlyfansAssetsV2,forwardListHidden,ugcDelete"
)
DEFAULT_ALL_WEB_LOCATION = "333.1365"
DEFAULT_DETAIL_FEATURES = "htmlNewStyle,itemOpusStyle,decorationCard"


def _normalized(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise InvalidParameterError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise InvalidParameterError(f"{name} cannot be blank")
    return value


def _dynamic_id(value: str, name: str = "dynamic_id") -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value


def all_query(
    *,
    features: str = DEFAULT_ALL_FEATURES,
    web_location: str = DEFAULT_ALL_WEB_LOCATION,
    host_mid: int | None = None,
    offset: str | None = None,
    update_baseline: str | None = None,
) -> dict[str, str]:
    params = {
        "features": _normalized(features, "features"),
        "web_location": _normalized(web_location, "web_location"),
    }
    if host_mid is not None:
        params["host_mid"] = integer(host_mid, "host_mid")
    if offset is not None:
        params["offset"] = _normalized(offset, "offset")
    if update_baseline is not None:
        params["update_baseline"] = _normalized(update_baseline, "update_baseline")
    return params


def check_new_query(update_baseline: str, *, dynamic_type: str | None = None) -> dict[str, str]:
    params = {"update_baseline": _normalized(update_baseline, "update_baseline")}
    if dynamic_type is not None:
        params["type"] = _normalized(dynamic_type, "type")
    return params


def nav_feed_query(
    *, update_baseline: str | None = None, offset: str | None = None
) -> dict[str, str]:
    params: dict[str, str] = {}
    if update_baseline is not None:
        params["update_baseline"] = _normalized(update_baseline, "update_baseline")
    if offset is not None:
        params["offset"] = _normalized(offset, "offset")
    return params


def detail_query(dynamic_id: str, *, features: str = DEFAULT_DETAIL_FEATURES) -> dict[str, str]:
    return {"id": _dynamic_id(dynamic_id), "features": _normalized(features, "features")}


def offset_query(dynamic_id: str, *, offset: str | None = None) -> dict[str, str]:
    params = {"id": _dynamic_id(dynamic_id)}
    if offset is not None:
        params["offset"] = _normalized(offset, "offset")
    return params


def id_query(dynamic_id: str) -> dict[str, str]:
    return {"id": _dynamic_id(dynamic_id)}


def lottery_query(business_id: str, *, csrf: str) -> dict[str, str]:
    return {
        "business_id": _dynamic_id(business_id, "business_id"),
        "business_type": "1",
        "csrf": csrf,
    }


def live_users_query(*, size: int | None = None) -> dict[str, str]:
    if size is None:
        return {}
    if type(size) is not int or size <= 0 or size > 2**32 - 1:
        raise InvalidParameterError("size must be a non-zero u32 integer")
    return {"size": str(size)}


def up_users_query(*, teenagers_mode: bool = False) -> dict[str, str]:
    if type(teenagers_mode) is not bool:
        raise InvalidParameterError("teenagers_mode must be a boolean")
    return {"teenagers_mode": "1" if teenagers_mode else "0"}


def like_body(dyn_id_str: str, up: int) -> dict[str, object]:
    if type(up) is not int or not 0 <= up <= 2:
        raise InvalidParameterError("up must be 0, 1, or 2")
    return {
        "dyn_id_str": _normalized(dyn_id_str, "dyn_id_str"),
        "up": up,
        "spmid": "333.1369.0.0",
        "from_spmid": "333.999.0.0",
    }


def delete_draft_form(draft_id: str, *, csrf: str) -> dict[str, str]:
    return {"draft_id": _normalized(draft_id, "draft_id"), "csrf": csrf}


def top_body(dyn_str: str) -> dict[str, object]:
    return {"dyn_str": _normalized(dyn_str, "dyn_str")}


def upload_category(category: str) -> str:
    return _normalized(category, "category")


def text_content(content: str) -> str:
    return _normalized(content, "content")


def complex_body(
    scene: int,
    contents: Sequence[DynamicContentItem],
    *,
    pics: Sequence[DynamicCreatePic] | None = None,
    topic: DynamicTopic | None = None,
) -> dict[str, object]:
    if type(scene) is not int or scene not in (1, 2, 4):
        raise InvalidParameterError("scene must be 1, 2, or 4")
    if not contents:
        raise InvalidParameterError("contents must contain at least one item")
    if pics is not None and not pics:
        raise InvalidParameterError("pics must contain at least one picture")
    return {
        "dyn_req": {
            "attach_card": None,
            "content": {
                "contents": [item.model_dump(by_alias=True) for item in contents],
            },
            "meta": {"app_meta": {"from": "create.dynamic.web", "mobi_app": "web"}},
            "scene": scene,
            "pics": None if pics is None else [pic.model_dump(by_alias=True) for pic in pics],
            "topic": None if topic is None else topic.model_dump(by_alias=True),
            "option": None,
        }
    }
