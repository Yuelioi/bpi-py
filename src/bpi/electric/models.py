from __future__ import annotations

import builtins

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel


class ChargeVipInfo(ResponseModel):
    vip_due_msec: int = Field(alias="vipDueMsec")
    vip_status: int = Field(alias="vipStatus")
    vip_type: int = Field(alias="vipType")


class ChargeUser(ResponseModel):
    uname: str
    avatar: str
    mid: int
    pay_mid: int
    rank: int
    vip_info: ChargeVipInfo
    message: str


class ChargeMonthUpData(ResponseModel):
    count: int
    list: builtins.list[ChargeUser] = Field(default_factory=builtins.list)
    total_count: int


class VideoShowInfoHighLevel(ResponseModel):
    privilege_type: int
    title: str
    sub_title: str
    show_button: bool


class VideoShowInfo(ResponseModel):
    show: bool
    state: int
    title: str
    jump_url: str
    icon: str
    high_level: VideoShowInfoHighLevel
    with_qa_id: int


class VideoElecShowData(ResponseModel):
    show_info: VideoShowInfo
    av_count: int
    count: int
    total_count: int
    list: builtins.list[ChargeUser] = Field(default_factory=builtins.list)


class RechargePage(ResponseModel):
    current_page: int = Field(alias="currentPage")
    page_size: int = Field(alias="pageSize")
    total_count: int = Field(alias="totalCount")
    total_page: int = Field(alias="totalPage")


class RechargeRecord(ResponseModel):
    mid: int
    name: str
    avatar: str
    original_third_coin: float = Field(alias="originalThirdCoin")
    brokerage: float
    remark: str
    ctime: str


class RechargeData(ResponseModel):
    page: RechargePage
    result: builtins.list[RechargeRecord]


class ElecRankPager(ResponseModel):
    current: int
    size: int
    total: int


class ElecRankRecord(ResponseModel):
    aid: int
    bvid: str
    elec_num: float
    title: str
    uname: str
    avatar: str
    ctime: str


class ElecRankData(ResponseModel):
    list: builtins.list[ElecRankRecord]
    pager: ElecRankPager


class Renew(ResponseModel):
    uid: int
    ruid: int
    goods_id: int
    status: int
    next_execute_time: int
    signed_time: int
    signed_price: int
    pay_channel: int
    period: int
    mobile_app: str


class ChargeItem(ResponseModel):
    privilege_type: int
    icon: str
    name: str
    expire_time: int
    renew: Renew | None
    start_time: int
    renew_list: builtins.list[Renew] | None


class ChargeUp(ResponseModel):
    up_uid: int
    user_name: str
    user_face: str
    item: builtins.list[ChargeItem]
    start: int
    high_level_state: int
    elec_reply_state: int


class ChargeRecordData(ResponseModel):
    list: builtins.list[ChargeUp] | None
    page: int
    page_size: int
    total_page: int
    total_num: int
    is_more: int


class UpowerRankUser(ResponseModel):
    rank: int
    mid: int
    nickname: str
    avatar: str


class UpowerRank(ResponseModel):
    total: int
    total_desc: str
    list: builtins.list[UpowerRankUser]


class ItemDetailIntro(ResponseModel):
    intro_video_aid: str
    welcomes: str


class UpUserCard(ResponseModel):
    avatar: str
    nickname: str


class UpowerItemDetail(ResponseModel):
    upower_rank: UpowerRank
    item: ItemDetailIntro
    user_card: UpUserCard
    upower_level: int
    elec_reply_state: int
    voucher_state: JsonValue
    upower_right_count: dict[str, int]
    only_contain_medal: bool
    privilege_type: int


class UpCard(ResponseModel):
    mid: int
    nickname: str
    official_title: str
    avatar: str


class UserCard(ResponseModel):
    avatar: str
    nickname: str


class ChallengeInfo(ResponseModel):
    challenge_id: str
    description: str
    challenge_type: int
    remaining_days: int
    end_time: str
    progress: int
    targets: builtins.list[JsonValue]
    state: int
    end_time_unix: int
    pub_dyn: int
    dyn_content: str


class ChargeFollowInfo(ResponseModel):
    days: int
    up_card: UpCard
    user_card: UserCard
    remain_days: int
    remain_less_1day: int
    upower_rank: UpowerRank
    upower_icon: str
    upower_right_count: int
    only_contain_medal: bool
    privilege_type: int
    challenge_info: ChallengeInfo


class UpInfo(ResponseModel):
    mid: int
    nickname: str
    avatar: str
    type: int
    title: str
    upower_state: int


class RankInfo(ResponseModel):
    mid: int
    nickname: str
    avatar: str
    rank: int
    day: int
    expire_at: int
    remain_days: int


class MemberUserInfo(ResponseModel):
    mid: int
    nickname: str
    avatar: str
    rank: int
    day: int
    expire_at: int
    remain_days: int


class LevelInfo(ResponseModel):
    privilege_type: int
    name: str
    price: int
    member_total: int


class MemberRankData(ResponseModel):
    up_info: UpInfo
    rank_info: builtins.list[RankInfo]
    user_info: MemberUserInfo
    member_total: int
    privilege_type: int
    is_charge: bool
    tabs: builtins.list[int]
    level_info: builtins.list[LevelInfo]


class ElecRemarkPager(ResponseModel):
    current: int
    size: int
    total: int


class ElecRemarkRecord(ResponseModel):
    aid: int
    bvid: str
    id: int
    mid: int
    reply_mid: int
    elec_num: int
    state: int
    msg: str
    aname: str
    uname: str
    avator: str
    reply_name: str
    reply_avator: str
    reply_msg: str
    ctime: int
    reply_time: int


class ElecRemarkList(ResponseModel):
    list: builtins.list[ElecRemarkRecord]
    pager: ElecRemarkPager


class ElecRemarkDetail(ElecRemarkRecord):
    pass


class BcoinQuickPayData(ResponseModel):
    mid: int
    up_mid: int
    order_no: str
    bp_num: str
    exp: int
    status: int
    msg: str
