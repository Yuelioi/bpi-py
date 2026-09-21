from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from .models import HeaderData, OnlineData, RegionBannerData
from .params import header_page_query, region_banner_query

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_REGION_BANNER = TypeAdapter(RegionBannerData)
_HEADER = TypeAdapter(HeaderData)
_ONLINE = TypeAdapter(OnlineData)


class WebWidgetClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def region_banner(self, *, region_id: int) -> RegionBannerData:
        return await self._client._get_payload(
            "/x/web-show/region/banner",
            region_banner_query(region_id),
            _REGION_BANNER,
        )

    async def header_page(self, *, resource_id: int = 142) -> HeaderData:
        header = await self._client._get_payload(
            "/x/web-show/page/header",
            header_page_query(resource_id),
            _HEADER,
        )
        header.parse_split_layer()
        return header

    async def online(self) -> OnlineData:
        return await self._client._get_payload(
            "/x/web-interface/online",
            {},
            _ONLINE,
        )
