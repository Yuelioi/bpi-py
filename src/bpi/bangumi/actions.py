from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from bpi._core.params import integer

from .models import BangumiFollowResult

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_FOLLOW = TypeAdapter(BangumiFollowResult)


class BangumiActionMethods:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def follow(self, *, season_id: int) -> BangumiFollowResult:
        form = {
            "season_id": integer(season_id, "season_id"),
            "csrf": self._client.csrf(),
        }
        return await self._client._post_payload("/pgc/web/follow/add", {}, _FOLLOW, form=form)

    async def unfollow(self, *, season_id: int) -> BangumiFollowResult:
        form = {
            "season_id": integer(season_id, "season_id"),
            "csrf": self._client.csrf(),
        }
        return await self._client._post_payload("/pgc/web/follow/del", {}, _FOLLOW, form=form)
