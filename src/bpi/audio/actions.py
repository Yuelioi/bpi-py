"""Source-derived audio writes; no automatic retries or live session loading."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from pydantic import ConfigDict, JsonValue, TypeAdapter

from bpi._core.params import integer
from bpi._core.response import ResponseModel
from bpi.errors import InvalidParameterError

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


class PromptData(ResponseModel):
    prompt: bool


_PROMPT = TypeAdapter(PromptData)
_BOOL = TypeAdapter(bool, config=ConfigDict(strict=True))
_STRING = TypeAdapter(str, config=ConfigDict(strict=True))
_OPTIONAL: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


def _media_ids(values: Sequence[str], name: str) -> str:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise InvalidParameterError(f"{name} must be a sequence of strings")
    result = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise InvalidParameterError(f"{name} must contain nonblank strings")
        result.append(value.strip())
    return ",".join(result)


def _action(value: int, name: str) -> str:
    result = integer(value, name)
    if value not in (1, 2):
        raise InvalidParameterError(f"{name} must be 1 or 2")
    return result


class AudioActionMethods:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def favorite(
        self,
        *,
        rid: int,
        add_media_ids: Sequence[str] = (),
        del_media_ids: Sequence[str] = (),
    ) -> PromptData:
        """Add/remove an audio item from favorite folders; folder IDs are strings."""
        form = {"rid": integer(rid, "rid"), "type": "12"}
        add = _media_ids(add_media_ids, "add_media_ids")
        remove = _media_ids(del_media_ids, "del_media_ids")
        if not add and not remove:
            raise InvalidParameterError("Provide at least one add or delete media ID")
        if add:
            form["add_media_ids"] = add
        if remove:
            form["del_media_ids"] = remove
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/medialist/gateway/coll/resource/deal",
            {},
            _PROMPT,
            form=form,
        )

    async def collect(self, *, sid: int, cids: int) -> bool:
        """Add a song to an audio collection; cids is one positive collection ID."""
        form = {"sid": integer(sid, "sid"), "cids": integer(cids, "cids")}
        form["csrf"] = self._client._csrf(host="www.bilibili.com")
        return await self._client._post_payload(
            "/audio/music-service-c/web/collections/songs-coll",
            {},
            _BOOL,
            host="www.bilibili.com",
            form=form,
        )

    async def coin(self, *, sid: int, multiply: int) -> str:
        """Spend one or two coins on a song and return the string payload."""
        form = {"sid": integer(sid, "sid"), "multiply": _action(multiply, "multiply")}
        form["csrf"] = self._client._csrf(host="www.bilibili.com")
        return await self._client._post_payload(
            "/audio/music-service-c/web/coin/add",
            {},
            _STRING,
            host="www.bilibili.com",
            form=form,
        )

    async def subscribe_rank(self, *, state: int, list_id: int | None = None) -> JsonValue:
        """Update ranking subscription state (1 or 2), optionally for one list."""
        form = {"state": _action(state, "state")}
        if list_id is not None:
            form["list_id"] = integer(list_id, "list_id")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/copyright-music-publicity/toplist/subscribe/update",
            {},
            _OPTIONAL,
            form=form,
            optional=True,
        )
