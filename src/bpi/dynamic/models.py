from __future__ import annotations

from typing import Annotated

from pydantic import BeforeValidator, Field, JsonValue

from bpi._core.response import ResponseModel


def _integer_from_text(value: object) -> object:
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return value
    return value


def _dynamic_id_text(value: object) -> object:
    if value is None:
        return ""
    if type(value) is int:
        return str(value)
    return value


IntFromText = Annotated[int, BeforeValidator(_integer_from_text)]
DynamicIdText = Annotated[str, BeforeValidator(_dynamic_id_text)]


class DynamicBasic(ResponseModel):
    comment_id_str: str
    comment_type: int
    like_icon: JsonValue
    rid_str: str
    editable: bool | None = None
    is_only_fans: bool | None = None
    jump_url: str | None = None


class DynamicAllItem(ResponseModel):
    basic: DynamicBasic
    id_str: str
    modules: JsonValue
    type_field: str = Field(alias="type")
    visible: bool


class DynamicAllData(ResponseModel):
    has_more: bool
    items: list[DynamicAllItem]
    offset: str
    update_baseline: str
    update_num: IntFromText


class DynamicUpdateData(ResponseModel):
    update_num: int


class DynamicNavAuthor(ResponseModel):
    face: str
    mid: IntFromText
    name: str


class DynamicNavItem(ResponseModel):
    author: DynamicNavAuthor
    cover: str
    id_str: str
    pub_time: str
    rid: IntFromText
    title: str
    type_num: int = Field(alias="type")
    visible: bool


class DynamicNavData(ResponseModel):
    has_more: bool
    items: list[DynamicNavItem]
    offset: str
    update_baseline: str
    update_num: IntFromText


class DynamicBanner(ResponseModel):
    banner_id: int
    end_time: int
    img_url: str
    link: str
    platform: int
    position: str
    start_time: int
    title: str
    weight: int


class DynamicBannerData(ResponseModel):
    banners: list[DynamicBanner]


class DynamicDetailItem(ResponseModel):
    id_str: DynamicIdText
    basic: DynamicBasic
    modules: JsonValue
    orig: DynamicDetailItem | None = None
    type_field: str = Field(alias="type")
    visible: bool


class DynamicDetailData(ResponseModel):
    item: DynamicDetailItem


class DynamicReactionItem(ResponseModel):
    action: str
    attend: int
    desc: str
    face: str
    mid: str
    name: str


class DynamicReactionData(ResponseModel):
    has_more: bool
    items: list[DynamicReactionItem]
    offset: str
    total: int


class LotteryWinner(ResponseModel):
    uid: int
    name: str
    face: str
    hongbao_money: float | None = None


class DynamicLotteryResult(ResponseModel):
    first_prize_result: list[LotteryWinner] = Field(default_factory=list)
    second_prize_result: list[LotteryWinner] = Field(default_factory=list)
    third_prize_result: list[LotteryWinner] = Field(default_factory=list)


class DynamicLotteryPrizeValue(ResponseModel):
    count: int
    stype: int


class DynamicLotteryPrizeType(ResponseModel):
    type_field: int = Field(alias="type")
    value: DynamicLotteryPrizeValue


class DynamicLotteryData(ResponseModel):
    lottery_id: int
    sender_uid: int
    business_type: int
    business_id: int
    status: int
    lottery_time: int
    participants: int
    first_prize: int
    first_prize_cmt: str
    first_prize_pic: str
    second_prize: int
    second_prize_cmt: str | None = None
    second_prize_pic: str
    third_prize: int
    third_prize_cmt: str | None = None
    third_prize_pic: str
    lottery_result: DynamicLotteryResult | None
    followed: bool
    has_charge_right: bool
    lottery_at_num: int
    lottery_detail_url: str
    lottery_feed_limit: int
    need_post: int
    participated: bool
    prize_type_first: DynamicLotteryPrizeType | None = None
    reposted: bool
    ts: int
    upower_redirect_url: str
    vip_batch_sign: str
    vip_redirect_url: str


class DynamicRichTextNode(ResponseModel):
    orig_text: str
    text: str
    type_field: str = Field(alias="type")


class DynamicForwardDesc(ResponseModel):
    rich_text_nodes: list[DynamicRichTextNode]
    text: str


class DynamicOfficial(ResponseModel):
    role: int
    title: str
    desc: str
    type_field: int = Field(alias="type")


class DynamicPendant(ResponseModel):
    pid: int
    name: str
    image: str
    expire: int
    image_enhance: str
    image_enhance_frame: str
    n_pid: int = 0


class DynamicVipLabel(ResponseModel):
    text: str
    label_theme: str
    text_color: str
    bg_style: int
    bg_color: str


class DynamicVip(ResponseModel):
    type_num: IntFromText = Field(alias="type")
    status: int
    due_date: IntFromText
    label: DynamicVipLabel
    nickname_color: str
    role: IntFromText
    tv_due_date: IntFromText
    tv_vip_pay_type: int
    tv_vip_status: int
    vip_pay_type: int


class DynamicLevelInfo(ResponseModel):
    current_exp: int
    current_level: int
    current_min: int
    next_exp: IntFromText


class DynamicForwardUser(ResponseModel):
    face: str
    face_nft: bool
    mid: int
    name: str
    official: DynamicOfficial
    pendant: DynamicPendant
    vip: DynamicVip


class DynamicForwardItem(ResponseModel):
    desc: DynamicForwardDesc
    id_str: str
    pub_time: str
    user: DynamicForwardUser


class DynamicForwardData(ResponseModel):
    has_more: bool
    items: list[DynamicForwardItem]
    offset: str
    total: int


class DynamicForwardInfoData(ResponseModel):
    item: DynamicForwardItem


class DynamicPic(ResponseModel):
    height: int
    size: float
    src: str
    width: int


class LiveUser(ResponseModel):
    face: str
    link: str
    title: str
    uid: int
    uname: str


class LiveUsersData(ResponseModel):
    count: int
    group: str
    items: list[LiveUser]


class DynamicUpUserInfo(ResponseModel):
    uid: int
    uname: str
    face: str


class DynamicUpUserProfile(ResponseModel):
    info: DynamicUpUserInfo


class DynUpUser(ResponseModel):
    user_profile: DynamicUpUserProfile


class DynUpUsersData(ResponseModel):
    button_statement: str
    items: list[DynUpUser]


class RecentMyInfo(ResponseModel):
    dyns: IntFromText
    face: str
    follower: str
    following: IntFromText
    level_info: DynamicLevelInfo
    mid: IntFromText
    name: str
    official: DynamicOfficial
    space_bg: str
    vip: DynamicVip


class RecentUpUser(ResponseModel):
    face: str
    has_update: bool
    is_reserve_recall: bool
    mid: IntFromText
    uname: str


class RecentUpData(ResponseModel):
    live_users: JsonValue | None
    my_info: RecentMyInfo | None
    up_list: list[RecentUpUser]


class UploadPicData(ResponseModel):
    image_url: str
    image_width: int
    image_height: int
    img_size: float


class CreateDynamicData(ResponseModel):
    dynamic_id: int
    dynamic_id_str: str


class CreateComplexDynamicData(ResponseModel):
    dyn_id: int
    dyn_id_str: str
    dyn_type: int


class DynamicContentItem(ResponseModel):
    type_num: int = Field(alias="type")
    biz_id: str | None = None
    raw_text: str


class DynamicCreatePic(ResponseModel):
    img_src: str
    img_height: int
    img_width: int
    img_size: float


class DynamicTopic(ResponseModel):
    id: int
    name: str
    from_source: str | None = None
    from_topic_id: int | None = None
