from __future__ import annotations

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel


class HistoryCursor(ResponseModel):
    max: int
    view_at: int
    business: str
    ps: int


class HistoryTab(ResponseModel):
    type_name: str = Field(alias="type")
    name: str


class HistoryDetail(ResponseModel):
    oid: int
    epid: int | None = None
    bvid: str | None = None
    page: int | None = None
    cid: int | None = None
    part: str | None = None
    business: str
    dt: int


class HistoryListItem(ResponseModel):
    title: str
    badge: str | None = None
    long_title: str | None = None
    cover: str | None = None
    covers: list[str] | None = None
    uri: str | None = None
    history: HistoryDetail
    videos: int | None = None
    author_name: str | None = None
    author_face: str | None = None
    author_mid: int | None = None
    view_at: int
    progress: int
    show_title: str | None = None
    duration: int | None = None
    current: str | None = None
    total: int | None = None
    new_desc: str | None = None
    is_finish: int | None = None
    is_fav: int
    kid: int
    tag_name: str | None = None
    live_status: int | None = None


class HistoryListData(ResponseModel):
    cursor: HistoryCursor
    tab: list[HistoryTab]
    list: list[HistoryListItem]


class ToViewRights(ResponseModel):
    bp: int
    elec: int
    download: int
    movie: int
    pay: int
    arc_pay: int | None = None
    hd5: int
    no_reprint: int
    autoplay: int
    ugc_pay: int
    is_cooperation: int
    ugc_pay_preview: int
    pay_free_watch: int | None = None
    no_background: int


class ToViewOwner(ResponseModel):
    mid: int
    name: str
    face: str


class ToViewStat(ResponseModel):
    aid: int
    view: int
    danmaku: int
    reply: int
    favorite: int
    coin: int
    share: int
    now_rank: int
    his_rank: int
    like: int
    like_g: int | None = None
    dislike: int
    fav_g: int | None = None
    vt: int
    vv: int


class ToViewDimension(ResponseModel):
    width: int
    height: int
    rotate: int


class ToViewPage(ResponseModel):
    cid: int
    page: int
    from_field: str = Field(alias="from")
    part: str
    duration: int
    vid: str
    weblink: str
    dimension: ToViewDimension
    ctime: int | None = None


class ToViewVideoItem(ResponseModel):
    aid: int
    videos: int
    tid: int
    tidv2: int | None = None
    tname: str
    tnamev2: str | None = None
    copyright: int
    pic: str
    cover43: str | None = None
    title: str
    long_title: str | None = None
    pubdate: int
    ctime: int
    desc: str
    state: int
    arc_state: int | None = None
    attribute: int | None = None
    duration: int
    rights: ToViewRights
    owner: ToViewOwner
    stat: ToViewStat
    dynamic: str | None = None
    dimension: ToViewDimension
    page: ToViewPage | None = None
    count: int | None = None
    cid: int
    progress: int
    add_at: int
    bvid: str
    uri: str | None = None
    short_link_v2: str | None = None
    season_title: str | None = None
    pgc_label: str | None = None
    c_source: str | None = None
    card_type: int | None = None
    enable_vt: int | None = None
    forbid_fav: bool | None = None
    forbid_sort: bool | None = None
    show_up: bool | None = None
    index_title: str | None = None
    left_icon_type: int | None = None
    left_text: str | None = None
    right_icon_type: int | None = None
    right_text: str | None = None
    pid_v2: int | None = None
    pid_name_v2: str | None = None
    up_from_v2: int | None = None
    view_text_1: str | None = None
    translate_info: JsonValue | None = None


class ToViewListData(ResponseModel):
    count: int
    list: list[ToViewVideoItem]
