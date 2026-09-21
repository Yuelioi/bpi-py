from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from .models import (
    ArchiveCompareData,
    ArchiveVideosData,
    ArticleTrendItem,
    ElectromagneticInfo,
    Episode,
    EpisodeAdd,
    EpisodeEdit,
    EpisodeSort,
    PlaySourceData,
    SeasonByAidData,
    SeasonEdit,
    SeasonInfoData,
    SeasonListData,
    SeasonSectionEdit,
    SeasonSectionEpisodesData,
    SeasonSectionSort,
    SectionSort,
    SpArchivesData,
    UpArticleStatData,
    UploadCoverData,
    UpStatData,
    VideoTrendItem,
    ViewerData,
)
from .params import (
    SeasonListOrder,
    SeasonListSort,
    UpArticleTrendMetric,
    UpVideoTrendMetric,
    archive_compare_query,
    archive_videos_query,
    archives_list_query,
    article_delete_form,
    article_trend_query,
    cover_data_uri,
    dynamic_delete_body,
    episodes_add_body,
    season_create_form,
    season_delete_form,
    season_edit_body,
    season_enable_section_form,
    season_id_query,
    season_list_query,
    season_section_edit_body,
    season_section_episode_edit_body,
    video_trend_query,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_SEASON_LIST = TypeAdapter(SeasonListData)
_SEASON_INFO = TypeAdapter(SeasonInfoData)
_SEASON_BY_AID = TypeAdapter(SeasonByAidData)
_SEASON_SECTION = TypeAdapter(SeasonSectionEpisodesData)
_ARCHIVES_LIST = TypeAdapter(SpArchivesData)
_ARCHIVE_VIDEOS = TypeAdapter(ArchiveVideosData)
_UP_STAT = TypeAdapter(UpStatData)
_ARCHIVE_COMPARE = TypeAdapter(ArchiveCompareData)
_ARTICLE_STAT = TypeAdapter(UpArticleStatData)
_VIDEO_TREND = TypeAdapter(list[VideoTrendItem])
_ARTICLE_TREND: TypeAdapter[list[ArticleTrendItem] | None] = TypeAdapter(
    list[ArticleTrendItem] | None
)
_PLAY_SOURCE: TypeAdapter[PlaySourceData | None] = TypeAdapter(PlaySourceData | None)
_VIEWER_DATA = TypeAdapter(ViewerData)
_ELECTROMAGNETIC_INFO = TypeAdapter(ElectromagneticInfo)
_UPLOAD_COVER = TypeAdapter(UploadCoverData)
_OPTIONAL_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_INT = TypeAdapter(int)


class CreativeCenterClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def season_list(
        self,
        *,
        pn: int,
        ps: int,
        order: SeasonListOrder | str | None = None,
        sort: SeasonListSort | str | None = None,
    ) -> SeasonListData:
        return await self._client._get_payload(
            "/x2/creative/web/seasons",
            season_list_query(pn, ps, order, sort),
            _SEASON_LIST,
            host="member.bilibili.com",
        )

    async def season_info(self, *, season_id: int) -> SeasonInfoData:
        return await self._client._get_payload(
            "/x2/creative/web/season",
            season_id_query(season_id),
            _SEASON_INFO,
            host="member.bilibili.com",
        )

    async def season_by_aid(self, *, aid: int) -> SeasonByAidData:
        return await self._client._get_payload(
            "/x2/creative/web/season/aid",
            season_id_query(aid, "aid"),
            _SEASON_BY_AID,
            host="member.bilibili.com",
        )

    async def season_section_episodes(self, *, season_id: int) -> SeasonSectionEpisodesData:
        return await self._client._get_payload(
            "/x2/creative/web/season/section",
            season_id_query(season_id),
            _SEASON_SECTION,
            host="member.bilibili.com",
        )

    async def archives_list(self, *, pn: int, ps: int | None = None) -> SpArchivesData:
        return await self._client._get_payload(
            "/x2/creative/web/archives/sp",
            archives_list_query(pn, ps),
            _ARCHIVES_LIST,
            host="member.bilibili.com",
        )

    async def archive_videos(self, *, aid: int) -> ArchiveVideosData:
        return await self._client._get_payload(
            "/x/web/archive/videos",
            archive_videos_query(aid),
            _ARCHIVE_VIDEOS,
            host="member.bilibili.com",
        )

    async def up_stat(self) -> UpStatData:
        return await self._client._get_payload(
            "/x/web/index/stat", {}, _UP_STAT, host="member.bilibili.com"
        )

    async def archive_compare(
        self, *, timestamp: int | None = None, size: int | None = None
    ) -> ArchiveCompareData:
        return await self._client._get_payload(
            "/x/web/data/archive_diagnose/compare",
            archive_compare_query(timestamp, size),
            _ARCHIVE_COMPARE,
            host="member.bilibili.com",
        )

    async def article_stat(self) -> UpArticleStatData:
        return await self._client._get_payload(
            "/x/web/data/article", {}, _ARTICLE_STAT, host="member.bilibili.com"
        )

    async def video_trend(self, *, metric: UpVideoTrendMetric | int) -> list[VideoTrendItem]:
        return await self._client._get_payload(
            "/x/web/data/pandect",
            video_trend_query(metric),
            _VIDEO_TREND,
            host="member.bilibili.com",
        )

    async def article_trend(
        self, *, metric: UpArticleTrendMetric | int
    ) -> list[ArticleTrendItem] | None:
        return await self._client._get_payload(
            "/x/web/data/article/thirty",
            article_trend_query(metric),
            _ARTICLE_TREND,
            host="member.bilibili.com",
            optional=True,
        )

    async def play_source(self) -> PlaySourceData | None:
        return await self._client._get_payload(
            "/x/web/data/playsource",
            {},
            _PLAY_SOURCE,
            host="member.bilibili.com",
            optional=True,
        )

    async def viewer_data(self) -> ViewerData:
        return await self._client._get_payload(
            "/x/web/data/base", {}, _VIEWER_DATA, host="member.bilibili.com"
        )

    async def electromagnetic_info(self) -> ElectromagneticInfo:
        return await self._client._get_payload(
            "/studio/up-rating/v3/rating/info", {}, _ELECTROMAGNETIC_INFO
        )

    async def dynamic_delete(self, *, dyn_id: str) -> JsonValue:
        body = dynamic_delete_body(dyn_id)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x/dynamic/feed/operate/remove",
            {"csrf": csrf},
            _OPTIONAL_JSON,
            json_body=body,
            optional=True,
        )

    async def article_delete(self, *, aid: int) -> JsonValue:
        form = article_delete_form(aid, csrf="")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/web/article/delete",
            {},
            _OPTIONAL_JSON,
            form=form,
            optional=True,
            host="member.bilibili.com",
        )

    async def upload_cover(self, *, mime_type: str, cover: str | Path) -> UploadCoverData:
        final_cover = cover_data_uri(mime_type, cover)
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/x/vu/web/cover/up",
            {},
            _UPLOAD_COVER,
            form={"csrf": csrf, "cover": final_cover},
            host="member.bilibili.com",
        )

    async def season_create(
        self,
        *,
        title: str,
        cover: str,
        desc: str | None = None,
        season_price: int | None = None,
    ) -> int:
        form = season_create_form(title, cover, desc=desc, season_price=season_price, csrf="")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x2/creative/web/season/add",
            {},
            _INT,
            form=form,
            host="member.bilibili.com",
        )

    async def season_delete(self, *, season_id: int) -> JsonValue:
        form = season_delete_form(season_id, csrf="")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x2/creative/web/season/del",
            {},
            _OPTIONAL_JSON,
            form=form,
            optional=True,
            host="member.bilibili.com",
        )

    async def season_episodes_add(
        self, *, section_id: int, episodes: Sequence[EpisodeAdd]
    ) -> JsonValue:
        body = episodes_add_body(section_id, episodes)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x2/creative/web/season/section/episodes/add",
            {"csrf": csrf},
            _OPTIONAL_JSON,
            json_body=body,
            optional=True,
            host="member.bilibili.com",
        )

    async def season_edit(
        self, *, season: SeasonEdit, sorts: Sequence[SeasonSectionSort]
    ) -> JsonValue:
        body = season_edit_body(season, sorts)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x2/creative/web/season/edit",
            {"csrf": csrf},
            _OPTIONAL_JSON,
            json_body=body,
            optional=True,
            host="member.bilibili.com",
        )

    async def season_section_edit(
        self, *, section: SeasonSectionEdit, sorts: Sequence[SectionSort]
    ) -> JsonValue:
        body = season_section_edit_body(section, sorts)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x2/creative/web/season/section/edit",
            {"csrf": csrf},
            _OPTIONAL_JSON,
            json_body=body,
            optional=True,
            host="member.bilibili.com",
        )

    async def season_section_episode_edit(
        self, *, episode: EpisodeEdit, sorts: Sequence[EpisodeSort]
    ) -> JsonValue:
        body = season_section_episode_edit_body(episode, sorts)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x2/creative/web/season/section/episode/edit",
            {"csrf": csrf},
            _OPTIONAL_JSON,
            json_body=body,
            optional=True,
            host="member.bilibili.com",
        )

    async def season_enable_section(self, *, season_id: int, enable: bool) -> JsonValue:
        form = season_enable_section_form(season_id, enable, csrf="")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x2/creative/web/season/section/switch",
            {},
            _OPTIONAL_JSON,
            form=form,
            optional=True,
            host="member.bilibili.com",
        )

    async def season_section_add_episodes(
        self, *, section_id: int, episodes: Sequence[Episode]
    ) -> JsonValue:
        body = episodes_add_body(section_id, episodes)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x2/creative/web/season/section/episodes/add",
            {"csrf": csrf},
            _OPTIONAL_JSON,
            json_body=body,
            optional=True,
            host="member.bilibili.com",
        )
