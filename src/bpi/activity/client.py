from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from .models import ActivityInfoData, ActivityListData
from .params import info_query, list_query

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_INFO = TypeAdapter(ActivityInfoData)
_LIST = TypeAdapter(ActivityListData)


class ActivityClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def info(self, *, sid: int, bvid: str | None = None) -> ActivityInfoData:
        return await self._client._get_payload(
            "/x/activity/subject/info",
            info_query(sid, bvid),
            _INFO,
        )

    async def list(
        self,
        *,
        platform_filter: str = "1,3",
        mold: int = 0,
        http_mode: int = 3,
        page: int = 1,
        page_size: int = 15,
    ) -> ActivityListData:
        return await self._client._get_payload(
            "/x/activity/page/list",
            list_query(platform_filter, mold, http_mode, page, page_size),
            _LIST,
        )

    async def list_default(self) -> ActivityListData:
        return await self.list()
