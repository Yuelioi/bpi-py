from __future__ import annotations

import base64
from collections.abc import Sequence
from enum import IntEnum, StrEnum
from pathlib import Path

from bpi._core.params import integer
from bpi.errors import InvalidParameterError

from .models import (
    Episode,
    EpisodeAdd,
    EpisodeEdit,
    EpisodeSort,
    SeasonEdit,
    SeasonSectionEdit,
    SeasonSectionSort,
    SectionSort,
)


class SeasonListOrder(StrEnum):
    CREATED_AT = "ctime"
    UPDATED_AT = "mtime"


class SeasonListSort(StrEnum):
    ASC = "asc"
    DESC = "desc"


class UpVideoTrendMetric(IntEnum):
    PLAY = 1
    DANMAKU = 2
    REPLY = 3
    SHARE = 4
    COIN = 5
    FAVORITE = 6
    CHARGE = 7
    LIKE = 8


class UpArticleTrendMetric(IntEnum):
    READ = 1
    REPLY = 2
    SHARE = 3
    COIN = 4
    FAVORITE = 5
    LIKE = 6


def _non_blank(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} cannot be blank")
    return value.strip()


def _string_enum(value: StrEnum | str, enum_type: type[StrEnum], name: str) -> str:
    if isinstance(value, enum_type):
        return value.value
    if isinstance(value, str):
        try:
            return enum_type(value).value
        except ValueError:
            pass
    allowed = ", ".join(item.value for item in enum_type)
    raise InvalidParameterError(f"{name} must be one of: {allowed}")


def _metric(value: IntEnum | int, enum_type: type[IntEnum], name: str) -> str:
    if isinstance(value, enum_type):
        return str(value.value)
    if type(value) is int:
        try:
            return str(enum_type(value).value)
        except ValueError:
            pass
    allowed = ", ".join(str(item.value) for item in enum_type)
    raise InvalidParameterError(f"{name} must be one of: {allowed}")


def season_list_query(
    pn: int,
    ps: int,
    order: SeasonListOrder | str | None = None,
    sort: SeasonListSort | str | None = None,
) -> dict[str, str]:
    query = {"pn": integer(pn, "pn"), "ps": integer(ps, "ps")}
    if order is not None:
        query["order"] = _string_enum(order, SeasonListOrder, "order")
    if sort is not None:
        query["sort"] = _string_enum(sort, SeasonListSort, "sort")
    return query


def season_id_query(value: int, name: str = "season_id") -> dict[str, str]:
    return {"id": integer(value, name)}


def archives_list_query(pn: int, ps: int | None = None) -> dict[str, str]:
    query = {"pn": integer(pn, "pn")}
    if ps is not None:
        query["ps"] = integer(ps, "ps")
    return query


def archive_videos_query(aid: int) -> dict[str, str]:
    return {"aid": integer(aid, "aid")}


def archive_compare_query(timestamp: int | None = None, size: int | None = None) -> dict[str, str]:
    query: dict[str, str] = {}
    if timestamp is not None:
        query["t"] = integer(timestamp, "timestamp")
    if size is not None:
        query["size"] = integer(size, "size")
    return query


def video_trend_query(metric: UpVideoTrendMetric | int) -> dict[str, str]:
    return {"type": _metric(metric, UpVideoTrendMetric, "metric")}


def article_trend_query(metric: UpArticleTrendMetric | int) -> dict[str, str]:
    return {"type": _metric(metric, UpArticleTrendMetric, "metric")}


def dynamic_delete_body(dyn_id: str) -> dict[str, object]:
    return {"dyn_id_str": _non_blank(dyn_id, "dyn_id")}


def article_delete_form(aid: int, *, csrf: str = "") -> dict[str, str]:
    return {"aid": integer(aid, "aid"), "csrf": csrf}


def cover_data_uri(mime_type: str, cover: str | Path) -> str:
    mime = _non_blank(mime_type, "mime_type")
    if isinstance(cover, Path):
        value = str(cover)
    elif isinstance(cover, str):
        value = cover.strip()
    else:
        raise InvalidParameterError("cover must be a data URI, base64 string, or file path")
    if not value:
        raise InvalidParameterError("cover cannot be blank")
    if value.startswith("data:"):
        return value
    if all(char.isascii() and (char.isalnum() or char in "+/=") for char in value):
        return f"data:{mime};base64,{value}"
    try:
        encoded = base64.b64encode(Path(value).read_bytes()).decode("ascii")
    except OSError:
        raise InvalidParameterError("cover file must be readable") from None
    return f"data:{mime};base64,{encoded}"


def season_create_form(
    title: str,
    cover: str,
    *,
    desc: str | None = None,
    season_price: int | None = None,
    csrf: str = "",
) -> dict[str, str]:
    form = {
        "title": _non_blank(title, "title"),
        "cover": _non_blank(cover, "cover"),
        "csrf": csrf,
    }
    if desc is not None:
        if not isinstance(desc, str):
            raise InvalidParameterError("desc must be a string")
        form["desc"] = desc
    if season_price is not None:
        form["season_price"] = integer(season_price, "season_price", minimum=0)
    return form


def season_delete_form(season_id: int, *, csrf: str = "") -> dict[str, str]:
    return {"id": integer(season_id, "season_id"), "csrf": csrf}


def episodes_add_body(
    section_id: int, episodes: Sequence[EpisodeAdd | Episode]
) -> dict[str, object]:
    section = int(integer(section_id, "section_id"))
    if not episodes:
        raise InvalidParameterError("episodes must contain at least one item")
    return {
        "sectionId": section,
        "episodes": [episode.model_dump(by_alias=True) for episode in episodes],
    }


def season_edit_body(
    season: SeasonEdit, sorts: Sequence[SeasonSectionSort]
) -> dict[str, object]:
    if not isinstance(season, SeasonEdit):
        raise InvalidParameterError("season must be a SeasonEdit")
    return {
        "season": season.model_dump(by_alias=True),
        "sorts": [item.model_dump(by_alias=True) for item in sorts],
    }


def season_section_edit_body(
    section: SeasonSectionEdit, sorts: Sequence[SectionSort]
) -> dict[str, object]:
    if not isinstance(section, SeasonSectionEdit):
        raise InvalidParameterError("section must be a SeasonSectionEdit")
    return {
        "section": section.model_dump(by_alias=True),
        "sorts": [item.model_dump(by_alias=True) for item in sorts],
    }


def season_section_episode_edit_body(
    episode: EpisodeEdit, sorts: Sequence[EpisodeSort]
) -> dict[str, object]:
    if not isinstance(episode, EpisodeEdit):
        raise InvalidParameterError("episode must be an EpisodeEdit")
    body: dict[str, object] = episode.model_dump(by_alias=True)
    body["sorts"] = [item.model_dump(by_alias=True) for item in sorts]
    return body


def season_enable_section_form(
    season_id: int, enable: bool, *, csrf: str = ""
) -> dict[str, str]:
    if type(enable) is not bool:
        raise InvalidParameterError("enable must be a boolean")
    return {
        "csrf": csrf,
        "season_id": integer(season_id, "season_id"),
        "no_section": "0" if enable else "1",
    }
