from __future__ import annotations

import builtins
from typing import TypeAlias

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel


class ArticleStats(ResponseModel):
    coin: int
    dislike: int
    dynamic: int
    favorite: int
    like: int
    reply: int
    share: int
    view: int


class ArticleCategory(ResponseModel):
    id: int
    name: str
    parent_id: int


class AuthorOfficialVerify(ResponseModel):
    type: int
    desc: str


class AuthorVip(ResponseModel):
    type: int
    status: int
    due_date: int
    vip_pay_type: int
    theme_type: int
    label: JsonValue | None = None


class ArticleNameplate(ResponseModel):
    nid: int
    name: str
    image: str
    image_small: str
    level: str
    condition: str


class ArticlePendant(ResponseModel):
    pid: int
    name: str
    image: str
    expire: int
    image_enhance: str = ""
    image_enhance_frame: str = ""
    n_pid: int | None = None


class ArticleAuthor(ResponseModel):
    mid: int
    name: str
    face: str
    level: int
    fans: int
    official_verify: AuthorOfficialVerify
    nameplate: ArticleNameplate
    pendant: ArticlePendant
    vip: AuthorVip


class ArticleMedia(ResponseModel):
    area: str
    cover: str
    media_id: int
    score: int
    season_id: int
    spoiler: int
    title: str
    type_id: int
    type_name: str


class ShareChannel(ResponseModel):
    name: str
    picture: str
    share_channel: str


class ArticleInfoData(ResponseModel):
    like: int
    attention: bool
    favorite: bool
    coin: int
    stats: ArticleStats
    title: str
    banner_url: str
    mid: int
    author_name: str
    is_author: bool
    image_urls: builtins.list[str]
    origin_image_urls: builtins.list[str]
    shareable: bool
    show_later_watch: bool
    show_small_window: bool
    in_list: bool
    pre: int
    next: int
    share_channels: builtins.list[ShareChannel]
    type: int
    video_url: str = ""
    location: str = ""
    disable_share: bool = False


class ArticleListData(ResponseModel):
    id: int
    name: str
    image_url: str
    update_time: int
    ctime: int
    publish_time: int
    summary: str
    words: int
    read: int
    articles_count: int
    state: int
    reason: str
    apply_time: str
    check_time: str
    mid: int | None = None


class ArticleTag(ResponseModel):
    tid: int
    name: str


class OpusAttribute(ResponseModel):
    align: str | None = None
    blockquote: bool | None = None
    bold: bool | None = None
    class_name: str | None = Field(default=None, alias="class")
    color: str | None = None
    header: int | None = None
    strike: bool | None = None
    link: str | None = None
    italic: bool | None = None
    list: str | None = None


class OpusImage(ResponseModel):
    alt: str
    url: str
    width: int
    height: int
    size: int
    status: str


class OpusCutOff(ResponseModel):
    type: str
    url: str


class OpusCard(ResponseModel):
    alt: str
    height: int
    id: str
    size: JsonValue | None = None
    status: str
    tid: int | float
    url: str
    width: int


class OpusRichInsert(ResponseModel):
    native_image: OpusImage | None = None
    cut_off: OpusCutOff | None = None
    video_card: OpusCard | None = None
    article_card: OpusCard | None = None
    vote_card: OpusCard | None = None
    live_card: OpusCard | None = None


class OpusOperation(ResponseModel):
    attribute: OpusAttribute | None = None
    insert: str | OpusRichInsert


class ArticleOpus(ResponseModel):
    ops: builtins.list[OpusOperation] = Field(default_factory=list)


class ArticleViewData(ResponseModel):
    act_id: int
    apply_time: str
    attributes: int | None = None
    authen_mark: JsonValue | None = Field(default=None, alias="authenMark")
    author: ArticleAuthor
    banner_url: str
    categories: builtins.list[ArticleCategory]
    category: ArticleCategory
    check_state: int
    check_time: str
    content: str
    content_pic_list: JsonValue | None = None
    cover_avid: int
    ctime: int
    dispute: JsonValue | None = None
    dyn_id_str: str
    dynamic: str | None = None
    id: int
    image_urls: builtins.list[str]
    is_like: bool
    keywords: str
    list: ArticleListData | None = None
    media: ArticleMedia
    mtime: int
    opus: ArticleOpus | None = None
    origin_image_urls: builtins.list[str]
    origin_template_id: int
    original: int
    private_pub: int
    publish_time: int
    reprint: int
    state: int
    stats: ArticleStats
    summary: str
    tags: builtins.list[ArticleTag]
    template_id: int
    title: str
    top_video_info: JsonValue | None = None
    total_art_num: int
    type: int
    version_id: int
    words: int


class ArticleItem(ResponseModel):
    id: int
    title: str
    state: int
    publish_time: int
    words: int
    image_urls: builtins.list[str]
    category: ArticleCategory
    categories: builtins.list[ArticleCategory]
    summary: str
    stats: ArticleStats | None = None
    like_state: int | None = None


class ArticlesData(ResponseModel):
    list: ArticleListData
    articles: builtins.list[ArticleItem]
    author: ArticleAuthor
    last: ArticleItem
    attention: bool


class VideoDimension(ResponseModel):
    height: int
    rotate: int
    width: int


class VideoOwner(ResponseModel):
    face: str
    mid: int
    name: str


class VideoRights(ResponseModel):
    arc_pay: int
    autoplay: int
    bp: int
    download: int
    elec: int
    hd5: int
    is_cooperation: int
    movie: int
    no_background: int
    no_reprint: int
    pay: int
    pay_free_watch: int
    ugc_pay: int
    ugc_pay_preview: int


class VideoStat(ResponseModel):
    aid: int
    coin: int
    danmaku: int
    dislike: int
    favorite: int
    his_rank: int
    like: int
    now_rank: int
    reply: int
    share: int
    view: int
    vt: int
    vv: int


class VideoCard(ResponseModel):
    aid: int
    bvid: str
    cid: int
    copyright: int
    pic: str
    ctime: int
    desc: str
    dimension: VideoDimension
    duration: int
    dynamic: str
    owner: VideoOwner
    pubdate: int
    rights: VideoRights
    short_link_v2: str
    stat: VideoStat
    state: int
    tid: int
    title: str
    tname: str
    videos: int
    vt_switch: bool


class ArticleCard(ResponseModel):
    act_id: int
    apply_time: str
    attributes: int
    authen_mark: JsonValue | None = Field(default=None, alias="authenMark")
    author: ArticleAuthor
    banner_url: str
    categories: builtins.list[ArticleCategory]
    category: ArticleCategory
    check_state: int
    check_time: str
    content_pic_list: JsonValue | None = None
    cover_avid: int
    ctime: int
    dispute: JsonValue | None = None
    dynamic: str
    id: int
    image_urls: builtins.list[str]
    is_like: bool
    list: ArticleListData | None = None
    media: ArticleMedia
    mtime: int
    origin_image_urls: builtins.list[str]
    origin_template_id: int
    original: int
    private_pub: int
    publish_time: int
    reprint: int
    state: int
    stats: ArticleStats
    summary: str
    template_id: int
    title: str
    top_video_info: JsonValue | None = None
    type: int
    words: int


class LiveCard(ResponseModel):
    area_v2_name: str
    cover: str
    face: str
    live_status: int
    online: int
    pendent_ru: str
    pendent_ru_color: str
    pendent_ru_pic: str
    role: int
    room_id: int
    title: str
    uid: int
    uname: str


CardItem: TypeAlias = VideoCard | ArticleCard | LiveCard | JsonValue
CardData: TypeAlias = dict[str, CardItem]


class CoinResponseData(ResponseModel):
    like: bool
