from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from .models import SpaceData
from .params import OpusSpaceFeedKind, space_feed_query

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_SPACE = TypeAdapter(SpaceData)


class OpusClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def space_feed(
        self,
        *,
        mid: int,
        page: int = 0,
        offset: str | None = None,
        kind: OpusSpaceFeedKind | str = OpusSpaceFeedKind.ALL,
    ) -> SpaceData:
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/opus/feed/space",
            space_feed_query(mid, page, offset, kind),
            _SPACE,
        )
