from __future__ import annotations

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel


class PopularListData(ResponseModel):
    list: list[JsonValue]
    no_more: bool


class PopularSeriesItem(ResponseModel):
    number: int
    subject: str
    status: int
    name: str


class PopularSeriesListData(ResponseModel):
    list: list[PopularSeriesItem]


class PopularSeriesConfig(ResponseModel):
    id: int
    type_name: str = Field(alias="type")
    number: int
    subject: str
    stime: int
    etime: int
    status: int
    name: str
    label: str
    hint: str
    color: int
    cover: str
    share_title: str
    share_subtitle: str
    media_id: int


class PopularSeriesOneData(ResponseModel):
    config: PopularSeriesConfig
    reminder: str | None = None
    list: list[JsonValue]


class PreciousVideoData(ResponseModel):
    title: str
    media_id: int
    explain: str
    list: list[JsonValue]


class RankingListData(ResponseModel):
    note: str
    list: list[JsonValue]


class RegionPage(ResponseModel):
    count: int
    num: int
    size: int


class RegionArchivesData(ResponseModel):
    archives: list[JsonValue]
    page: RegionPage


class NewListRankResult(ResponseModel):
    pub_date: str = Field(alias="pubdate")
    pic: str
    tag: str
    duration: int
    id: int
    rank_score: int | None = None
    badgepay: bool
    senddate: int | None = None
    author: str
    review: int
    mid: int
    is_union_video: int
    rank_index: int | None = None
    type_name: str = Field(alias="type")
    play: str
    video_review: int
    is_pay: int
    favorites: int
    arcurl: str
    bvid: str
    title: str
    description: str


class NewListRankData(ResponseModel):
    result: list[NewListRankResult] | None = None
    num_results: int = Field(alias="numResults")
    page: int
    pagesize: int
    msg: str
