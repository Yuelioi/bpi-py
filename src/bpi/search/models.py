from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel

T = TypeVar("T")


class LivePageInfo(ResponseModel):
    total: int
    num_results: int = Field(alias="numResults")
    pages: int
    num_pages: int = Field(alias="numPages")


class PageInfo(ResponseModel):
    live_user: LivePageInfo
    live_room: LivePageInfo


class SearchData(ResponseModel, Generic[T]):
    seid: str
    page: int
    page_size: int = Field(alias="pagesize")
    num_results: int = Field(alias="numResults")
    num_pages: int = Field(alias="numPages")
    result: T | None = None
    page_info: PageInfo | None = Field(default=None, alias="pageinfo")


class Article(ResponseModel):
    category_id: int
    category_name: str
    comment_url: str
    desc: str
    id: int
    image_urls: list[str]
    is_comment: int
    is_fold: bool
    is_rk1: bool
    like: int
    mid: int
    pub_time: int
    rank_index: int
    rank_offset: int
    reply: int
    spread_id: int
    sub_type: int
    template_id: int
    title: str
    type_field: str = Field(alias="type")
    version: str
    view: int


class Badge(ResponseModel):
    text: str
    text_color: str
    text_color_night: str
    bg_color: str
    bg_color_night: str
    border_color: str
    border_color_night: str
    bg_style: int


class MediaScore(ResponseModel):
    score: float
    user_count: int


class Episode(ResponseModel):
    id: int
    cover: str
    title: str
    url: str
    release_date: str
    badges: list[Badge]
    index_title: str
    long_title: str


class Bangumi(ResponseModel):
    type_field: str = Field(alias="type")
    media_id: int
    title: str
    org_title: str
    media_type: int
    cv: str
    staff: str
    season_id: int
    is_avid: bool
    hit_epids: str
    season_type: int
    season_type_name: str
    selection_style: str
    ep_size: int
    url: str
    button_text: str
    is_follow: int
    is_selection: int
    eps: list[Episode]
    badges: list[Badge]
    cover: str
    areas: str
    styles: str
    goto_url: str
    desc: str
    pubtime: int
    media_mode: int
    fix_pubtime_str: str
    media_score: MediaScore
    display_info: list[Badge]
    pgc_season_id: int
    corner: int
    index_show: str


class Movie(ResponseModel):
    type_field: str = Field(alias="type")
    media_id: int
    title: str
    org_title: str
    media_type: int
    cv: str
    staff: str
    season_id: int
    is_avid: bool
    hit_epids: str
    season_type: int
    season_type_name: str
    selection_style: str
    ep_size: int
    url: str
    button_text: str
    is_follow: int
    is_selection: int
    badges: list[Badge]
    cover: str
    areas: str
    styles: str
    goto_url: str
    desc: str
    pubtime: int
    media_mode: int
    fix_pubtime_str: str
    media_score: MediaScore
    display_info: list[Badge]
    pgc_season_id: int
    corner: int
    index_show: str


class Video(ResponseModel):
    type_field: str = Field(alias="type")
    id: int
    author: str
    mid: int
    typeid: str
    typename: str
    arcurl: str
    aid: int
    bvid: str
    title: str
    pic: str
    play: int
    danmaku: int
    favorites: int
    like: int
    tag: str
    review: int
    pubdate: int
    duration: str


class LiveUser(ResponseModel):
    area: int
    area_v2_id: int
    attentions: int
    cate_name: str
    hit_columns: list[str]
    is_live: bool
    live_status: int
    live_time: str
    rank_index: int
    rank_offset: int
    room_id: int = Field(alias="roomid")
    tags: str
    type_field: str = Field(alias="type")
    uface: str
    uid: int
    uname: str
    id: int | None = None


class WatchedShow(ResponseModel):
    switch: bool
    num: int
    text_small: str
    text_large: str
    icon: str
    icon_location: str
    icon_web: str


class LiveRoom(ResponseModel):
    area: int
    attentions: int
    cate_name: str
    cover: str
    is_live_room_inline: int
    live_status: int
    live_time: str
    online: int
    rank_index: int
    rank_offset: int
    roomid: int
    short_id: int
    tags: str
    title: str
    type_field: str = Field(alias="type")
    uface: str
    uid: int
    uname: str
    user_cover: str
    watched_show: WatchedShow | None = None


class LiveData(ResponseModel):
    live_room: list[LiveRoom]
    live_user: list[LiveUser]


class OfficialVerify(ResponseModel):
    type_field: int = Field(alias="type")
    desc: str


class BiliUserVideo(ResponseModel):
    aid: int
    bvid: str
    title: str
    pubdate: int
    arcurl: str
    pic: str
    play: str
    dm: int
    coin: int
    fav: int
    desc: str
    duration: str
    is_pay: int
    is_union_video: int
    is_charge_video: int
    vt: int
    enable_vt: int
    vt_display: str


class BiliUser(ResponseModel):
    type_field: str = Field(alias="type")
    mid: int
    uname: str
    usign: str
    fans: int
    videos: int
    upic: str
    face_nft: int
    face_nft_type: int
    verify_info: str
    level: int
    gender: int
    is_upuser: int
    is_live: int
    room_id: int
    res: list[BiliUserVideo]
    official_verify: OfficialVerify
    is_senior_member: int


class DefaultSearchData(ResponseModel):
    seid: str
    id: int
    type_field: int = Field(alias="type")
    show_name: str
    name: str | None = None
    goto_type: int
    goto_value: str
    url: str


class SearchSuggestItem(ResponseModel):
    value: str | None = None
    name: str | None = None
    item_type: str | None = Field(default=None, alias="type")


class SearchSuggest(ResponseModel):
    tag: list[SearchSuggestItem] | None = None


class HotWordItem(ResponseModel):
    hot_id: int
    keyword: str
    show_name: str
    heat_score: int
    word_type: int
    live_id: list[JsonValue] | None = None


class HotWordDataResponse(ResponseModel):
    code: int
    items: list[HotWordItem] = Field(alias="list")
