from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from .models import (
    NewListRankData,
    PopularListData,
    PopularSeriesListData,
    PopularSeriesOneData,
    PreciousVideoData,
    RankingListData,
    RegionArchivesData,
)
from .params import (
    VideoNewListRankOrder,
    VideoRankingType,
    popular_list_query,
    ranking_list_query,
    region_newlist_query,
    region_newlist_rank_query,
    region_query,
    region_tag_query,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_POPULAR = TypeAdapter(PopularListData)
_SERIES_LIST = TypeAdapter(PopularSeriesListData)
_SERIES_ONE = TypeAdapter(PopularSeriesOneData)
_PRECIOUS = TypeAdapter(PreciousVideoData)
_RANKING = TypeAdapter(RankingListData)
_REGION = TypeAdapter(RegionArchivesData)
_NEWLIST_RANK = TypeAdapter(NewListRankData)


class VideoRankingClient:
    """Video popularity, ranking, and region listing APIs."""

    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def popular_list(
        self, *, page: int | None = None, page_size: int | None = None
    ) -> PopularListData:
        return await self._client._get_payload(
            "/x/web-interface/popular", popular_list_query(page, page_size), _POPULAR
        )

    async def popular_series_list(self) -> PopularSeriesListData:
        return await self._client._get_payload(
            "/x/web-interface/popular/series/list", {}, _SERIES_LIST
        )

    async def popular_series_one(self, *, number: int) -> PopularSeriesOneData:
        if number <= 0 or type(number) is not int:
            from bpi.errors import InvalidParameterError

            raise InvalidParameterError("number must be an integer >= 1")
        params = await self._client._sign({"number": str(number)})
        return await self._client._get_payload(
            "/x/web-interface/popular/series/one", params, _SERIES_ONE
        )

    async def popular_precious(self) -> PreciousVideoData:
        return await self._client._get_payload("/x/web-interface/popular/precious", {}, _PRECIOUS)

    async def ranking_list(
        self,
        *,
        rid: int | None = None,
        ranking_type: VideoRankingType | str | None = None,
    ) -> RankingListData:
        return await self._client._get_payload(
            "/x/web-interface/ranking/v2",
            ranking_list_query(rid, ranking_type),
            _RANKING,
        )

    async def region_dynamic(
        self, *, rid: int, page: int | None = None, page_size: int | None = None
    ) -> RegionArchivesData:
        return await self._client._get_payload(
            "/x/web-interface/dynamic/region", region_query(rid, page, page_size), _REGION
        )

    async def region_tag_dynamic(
        self,
        *,
        rid: int,
        tag_id: int,
        page: int | None = None,
        page_size: int | None = None,
    ) -> RegionArchivesData:
        return await self._client._get_payload(
            "/x/web-interface/dynamic/tag",
            region_tag_query(rid, tag_id, page, page_size),
            _REGION,
        )

    async def region_newlist(
        self,
        *,
        rid: int,
        page: int | None = None,
        page_size: int | None = None,
        typ: int | None = None,
    ) -> RegionArchivesData:
        return await self._client._get_payload(
            "/x/web-interface/newlist",
            region_newlist_query(rid, page, page_size, typ),
            _REGION,
        )

    async def region_newlist_rank(
        self,
        *,
        cate_id: int,
        page_size: int,
        time_from: str,
        time_to: str,
        order: VideoNewListRankOrder | str | None = None,
        page: int | None = None,
    ) -> NewListRankData:
        return await self._client._get_payload(
            "/x/web-interface/newlist_rank",
            region_newlist_rank_query(cate_id, page_size, time_from, time_to, order, page),
            _NEWLIST_RANK,
        )
