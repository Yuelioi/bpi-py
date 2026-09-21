"""Video actions ported from video/action.rs, report.rs and collection/action.rs."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from bpi._core.params import integer
from bpi._core.response import ResponseModel
from bpi.errors import InvalidParameterError

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


class CoinData(ResponseModel):
    like: bool


class FavoriteData(ResponseModel):
    prompt: bool
    ga_data: JsonValue = None
    toast_msg: str | None = None
    success_num: int


class VideoCoinStatusData(ResponseModel):
    multiply: int


class CreateSeriesResponseData(ResponseModel):
    series_id: int


_COIN = TypeAdapter(CoinData)
_FAVORITE = TypeAdapter(FavoriteData)
_COIN_STATUS = TypeAdapter(VideoCoinStatusData)
_SERIES = TypeAdapter(CreateSeriesResponseData)
_OPTIONAL: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidParameterError(f"{name} must be a nonblank string")
    return value.strip()


def _legacy_ids(aid: int | None, bvid: str | None) -> dict[str, str]:
    # The Rust action API permits both IDs and accepts nonblank legacy BV strings.
    params = {}
    if aid is not None:
        params["aid"] = integer(aid, "aid")
    if bvid is not None:
        _text(bvid, "bvid")
        params["bvid"] = bvid
    if not params:
        raise InvalidParameterError("Provide aid or bvid")
    return params


def _action(value: int, name: str) -> str:
    result = integer(value, name)
    if value not in (1, 2):
        raise InvalidParameterError(f"{name} must be 1 or 2")
    return result


def _ids(values: Sequence[str], name: str) -> str:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise InvalidParameterError(f"{name} must be a sequence of strings")
    return ",".join(_text(value, name) for value in values)


def _series_form(mid: int, series_id: int) -> dict[str, str]:
    return {"mid": integer(mid, "mid"), "series_id": integer(series_id, "series_id")}


def _optional_text(form: dict[str, str], **values: str | None) -> None:
    for name, value in values.items():
        if value is not None:
            form[name] = _text(value, name)


class VideoActionMethods:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def coin_status(
        self,
        *,
        aid: int | None = None,
        bvid: str | None = None,
    ) -> VideoCoinStatusData:
        """Read the current account's coin count for a video."""
        return await self._client._get_payload(
            "/x/web-interface/archive/coins",
            _legacy_ids(aid, bvid),
            _COIN_STATUS,
        )

    async def like(
        self,
        *,
        like: int,
        aid: int | None = None,
        bvid: str | None = None,
    ) -> JsonValue:
        """Like (1) or unlike (2); requires a session with bili_jct."""
        form = _legacy_ids(aid, bvid)
        form["like"] = _action(like, "like")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/web-interface/archive/like",
            {},
            _OPTIONAL,
            form=form,
            optional=True,
        )

    async def coin(
        self,
        *,
        multiply: int,
        aid: int | None = None,
        bvid: str | None = None,
        select_like: bool = False,
    ) -> CoinData:
        """Spend one or two coins, optionally liking the video."""
        form = _legacy_ids(aid, bvid)
        form["multiply"] = _action(multiply, "multiply")
        if type(select_like) is not bool:
            raise InvalidParameterError("select_like must be a boolean")
        form["select_like"] = "1" if select_like else "0"
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/web-interface/coin/add",
            {},
            _COIN,
            form=form,
        )

    async def favorite(
        self,
        *,
        rid: int,
        add_media_ids: Sequence[str] = (),
        del_media_ids: Sequence[str] = (),
    ) -> FavoriteData:
        """Add/remove a video from the specified favorite folders."""
        form = {"rid": integer(rid, "rid"), "type": "2"}
        add = _ids(add_media_ids, "add_media_ids")
        delete = _ids(del_media_ids, "del_media_ids")
        if not add and not delete:
            raise InvalidParameterError("Provide at least one add or delete media ID")
        if add:
            form["add_media_ids"] = add
        if delete:
            form["del_media_ids"] = delete
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/v3/fav/resource/deal",
            {},
            _FAVORITE,
            form=form,
        )

    async def report_watch_progress(self, *, aid: int, cid: int, progress: int = 0) -> JsonValue:
        """Report watched seconds using the source multipart protocol."""
        form = {
            "aid": integer(aid, "aid"),
            "cid": integer(cid, "cid"),
            "progress": integer(progress, "progress", 0),
        }
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/v2/history/report",
            {},
            _OPTIONAL,
            form=form,
            multipart=True,
            optional=True,
        )

    async def create_collection_series(
        self,
        *,
        mid: int,
        name: str,
        keywords: str | None = None,
        description: str | None = None,
        aids: str | None = None,
    ) -> CreateSeriesResponseData:
        """Create a series; aids is a comma-separated archive ID string."""
        form = {"mid": integer(mid, "mid"), "name": _text(name, "name")}
        _optional_text(form, keywords=keywords, description=description, aids=aids)
        return await self._client._post_payload(
            "/x/series/series/createAndAddArchives",
            {"csrf": self._client.csrf()},
            _SERIES,
            form=form,
            multipart=True,
        )

    async def delete_collection_series(self, *, mid: int, series_id: int) -> JsonValue:
        """Delete a series; protocol parameters are in the POST query."""
        query = _series_form(mid, series_id)
        query.update(csrf=self._client.csrf(), aids="")
        return await self._client._post_payload(
            "/x/series/series/delete",
            query,
            _OPTIONAL,
            optional=True,
        )

    async def delete_collection_archives(
        self,
        *,
        mid: int,
        series_id: int,
        aids: str,
    ) -> JsonValue:
        """Remove comma-separated archive IDs from a series."""
        form = _series_form(mid, series_id)
        form["aids"] = _text(aids, "aids")
        return await self._client._post_payload(
            "/x/series/series/delArchives",
            {"csrf": self._client.csrf()},
            _OPTIONAL,
            form=form,
            optional=True,
        )

    async def add_collection_archives(
        self,
        *,
        mid: int,
        series_id: int,
        aids: str,
    ) -> JsonValue:
        """Add comma-separated archive IDs to a series."""
        form = _series_form(mid, series_id)
        form["aids"] = _text(aids, "aids")
        return await self._client._post_payload(
            "/x/series/series/addArchives",
            {"csrf": self._client.csrf()},
            _OPTIONAL,
            form=form,
            optional=True,
        )

    async def update_collection_series(
        self,
        *,
        mid: int,
        series_id: int,
        name: str,
        keywords: str | None = None,
        description: str | None = None,
        add_aids: str | None = None,
        del_aids: str | None = None,
    ) -> JsonValue:
        """Update series metadata and optional comma-separated archive IDs."""
        form = _series_form(mid, series_id)
        form["name"] = _text(name, "name")
        _optional_text(
            form, keywords=keywords, description=description, add_aids=add_aids, del_aids=del_aids
        )
        return await self._client._post_payload(
            "/x/series/series/update",
            {"csrf": self._client.csrf()},
            _OPTIONAL,
            form=form,
            multipart=True,
            optional=True,
        )
