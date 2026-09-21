from __future__ import annotations

from pydantic import Field, JsonValue, field_validator

from bpi._core.response import ResponseModel


class LiveSubArea(ResponseModel):
    id: str
    parent_id: str
    old_area_id: str
    name: str
    act_id: str
    pk_status: str
    hot_status: int
    lock_status: str
    pic: str
    parent_name: str
    area_type: int


class LiveParentArea(ResponseModel):
    id: int
    name: str
    list: list[LiveSubArea]


class RoomPendantFrame(ResponseModel):
    name: str
    value: str
    position: int
    desc: str
    area: int
    area_old: int
    bg_color: str
    bg_pic: str
    use_old_area: bool


class RoomPendantBadge(ResponseModel):
    name: str
    position: int
    value: str
    desc: str


class RoomPendants(ResponseModel):
    frame: RoomPendantFrame
    mobile_frame: RoomPendantFrame | None
    badge: RoomPendantBadge | None
    mobile_badge: RoomPendantBadge | None


class RoomInfoData(ResponseModel):
    uid: int
    room_id: int
    short_id: int
    attention: int
    online: int
    is_portrait: bool
    description: str
    live_status: int
    area_id: int
    parent_area_id: int
    parent_area_name: str
    old_area_id: int
    background: str
    title: str
    user_cover: str
    keyframe: str
    live_time: str
    tags: str
    room_silent_type: str
    room_silent_level: int
    room_silent_second: int
    area_name: str
    hot_words: list[str]
    hot_words_status: int
    new_pendants: RoomPendants
    pk_status: int
    pk_id: int
    allow_change_area_time: int
    allow_upload_cover_time: int
    studio_info: dict[str, JsonValue] | None


class QualityDescription(ResponseModel):
    qn: int
    desc: str


class LiveStreamUrl(ResponseModel):
    url: str
    order: int
    stream_type: int
    p2p_type: int


class LiveStreamData(ResponseModel):
    current_quality: int
    accept_quality: list[str]
    current_qn: int
    quality_description: list[QualityDescription]
    durl: list[LiveStreamUrl]


class WatchedShow(ResponseModel):
    switch: bool
    num: int
    text_small: str
    text_large: str
    icon: str
    icon_location: int
    icon_web: str


class RecommendRoom(ResponseModel):
    head_box: JsonValue | None = None
    area_v2_id: int
    area_v2_parent_id: int
    area_v2_name: str
    area_v2_parent_name: str
    broadcast_type: int
    cover: str
    link: str
    online: int
    pendant_info: JsonValue = Field(alias="pendant_Info")
    room_id: int = Field(alias="roomid")
    title: str
    uname: str
    face: str
    verify: JsonValue
    uid: int
    keyframe: str
    is_auto_play: int
    head_box_type: int
    flag: int
    session_id: str
    show_callback: str
    click_callback: str
    special_id: int
    watched_show: WatchedShow
    is_nft: int
    nft_dmark: str
    is_ad: bool
    ad_transparent_content: JsonValue | None = None
    show_ad_icon: bool
    status: bool
    followers: int


class RecommendData(ResponseModel):
    recommend_room_list: list[RecommendRoom]
    top_room_id: int


class PcLiveVersionData(ResponseModel):
    curr_version: str
    build: int
    instruction: str
    file_size: str
    file_md5: str
    content: str
    download_url: str
    hdiffpatch_switch: int


class GiftTypeItem(ResponseModel):
    gift_id: int
    gift_name: str
    price: int = 0


class GiftItem(ResponseModel):
    id: int
    name: str
    price: int
    type_name: int = Field(alias="type")
    coin_type: str
    effect: int
    stay_time: int
    animation_frame_num: int
    desc: str
    img_basic: str
    gif: str


class GiftConfig(ResponseModel):
    list: list[GiftItem]


class GiftBaseConfig(ResponseModel):
    base_config: GiftConfig


class RoomGiftData(ResponseModel):
    gift_config: GiftBaseConfig | None
    gift_data: JsonValue | None = None
    global_config: JsonValue | None = None


class BlindGiftItem(ResponseModel):
    gift_id: int
    price: int
    gift_name: str
    gift_img: str
    chance: str


class BlindGiftData(ResponseModel):
    note_text: str
    blind_price: int
    blind_gift_name: str
    gifts: list[BlindGiftItem]


class LiveDanmuInfoHost(ResponseModel):
    host: str
    port: int = 0
    wss_port: int = 0
    ws_port: int = 0


class LiveDanmuInfoData(ResponseModel):
    token: str = ""
    host_list: list[LiveDanmuInfoHost] = Field(default_factory=list)


class EmoticonItem(ResponseModel):
    bulge_display: int
    descript: str
    emoji: str
    emoticon_id: int
    emoticon_unique: str
    emoticon_value_type: int
    height: int
    identity: int
    in_player_area: int
    is_dynamic: int
    perm: int
    unlock_need_gift: int
    unlock_need_level: int
    unlock_show_color: str
    unlock_show_image: str
    unlock_show_text: str
    url: str
    width: int


class TopShowItem(ResponseModel):
    image: str
    text: str


class TopShow(ResponseModel):
    top_left: TopShowItem
    top_right: TopShowItem


class EmoticonPackage(ResponseModel):
    current_cover: str
    emoticons: list[EmoticonItem]
    pkg_descript: str
    pkg_id: int
    pkg_name: str
    pkg_perm: int
    pkg_type: int
    recently_used_emoticons: list[JsonValue]
    top_show: TopShow | None
    top_show_recent: TopShow | None
    unlock_identity: int
    unlock_need_gift: int


class EmoticonData(ResponseModel):
    data: list[EmoticonPackage]
    fans_brand: int
    purchase_url: str | None


class RedPocketAward(ResponseModel):
    gift_id: int
    num: int
    gift_name: str
    gift_pic: str


class PopularityRedPocket(ResponseModel):
    lot_id: int
    sender_uid: int
    sender_name: str
    sender_face: str
    join_requirement: int
    danmu: str
    awards: list[RedPocketAward]
    start_time: int
    end_time: int
    last_time: int
    remove_time: int
    replace_time: int
    current_time: int
    lot_status: int
    h5_url: str
    user_status: int
    lot_config_id: int
    total_price: int


class LotteryInfoData(ResponseModel):
    popularity_red_pocket: list[PopularityRedPocket] | None = None
    activity_box_info: dict[str, JsonValue] | None = None


class PageInfo(ResponseModel):
    total_page: int
    cur_page: int


class FansMedalItem(ResponseModel):
    can_delete: bool = Field(alias="can_deleted")
    day_limit: int
    guard_level: int
    guard_medal_title: str
    intimacy: int
    is_lighted: int
    level: int
    medal_name: str
    medal_color_border: int
    medal_color_start: int
    medal_color_end: int
    medal_id: int
    next_intimacy: int
    today_feed: int
    roomid: int
    status: int
    target_id: int
    target_name: str
    uname: str


class MyMedalsData(ResponseModel):
    count: int
    items: list[FansMedalItem]
    page_info: PageInfo


class FollowUpLiveItem(ResponseModel):
    roomid: int
    uid: int
    uname: str
    title: str
    face: str
    live_status: int
    record_live_time: int
    area_name_v2: str
    room_news: str
    text_small: str
    room_cover: str
    parent_area_id: int
    area_id: int


class FollowUpLiveData(ResponseModel):
    title: str
    page_size: int = Field(alias="pageSize")
    total_page: int = Field(alias="totalPage")
    count: int
    never_lived_count: int
    live_count: int
    never_lived_faces: list[str]
    list: list[FollowUpLiveItem]


class LiveRoom(ResponseModel):
    title: str
    room_id: int
    uid: int
    online: int
    live_time: int
    live_status: int
    short_id: int
    area: int
    area_name: str
    area_v2_id: int
    area_v2_name: str
    area_v2_parent_name: str
    area_v2_parent_id: int
    uname: str
    face: str
    tag_name: str
    tags: str
    cover_from_user: str
    keyframe: str
    lock_till: str
    hidden_till: str
    broadcast_type: int
    is_encrypt: bool
    link: str
    nickname: str
    roomname: str
    roomid: int


class LiveWebListData(ResponseModel):
    rooms: list[LiveRoom]
    list: list[LiveRoom]
    count: int
    not_living_num: int


class ReplayLiveInfo(ResponseModel):
    title: str
    cover: str
    live_time: int
    live_type: int


class ReplayVideoInfo(ResponseModel):
    replay_status: int
    estimated_time: str
    duration: int
    download_url: str | None
    alert_code: int | None
    alert_message: str | None


class ReplayAlarmInfo(ResponseModel):
    code: int
    message: str
    cur_time: int
    is_ban_publish: bool


class ReplayInfo(ResponseModel):
    replay_id: int
    live_info: ReplayLiveInfo
    video_info: ReplayVideoInfo
    alarm_info: ReplayAlarmInfo
    room_id: int
    live_key: str
    start_time: int
    end_time: int


class ReplayPagination(ResponseModel):
    page: int
    page_size: int
    total: int | None = None


class ReplayListData(ResponseModel):
    replay_info: list[ReplayInfo] | None = None
    pagination: ReplayPagination


class GuardTabInfo(ResponseModel):
    num: int
    page: int
    now: int
    achievement_level: int
    anchor_guard_achieve_level: int
    achievement_icon_src: str
    buy_guard_icon_src: str
    rule_doc_src: str
    ex_background_src: str
    color_start: str
    color_end: str
    tab_color: list[str]
    title_color: list[str]


class GuardUserOriginInfo(ResponseModel):
    name: str
    face: str


class GuardUserOfficialInfo(ResponseModel):
    role: int
    title: str
    desc: str
    type_name: int = Field(alias="type")


class GuardUserBaseInfo(ResponseModel):
    name: str
    face: str
    name_color: int
    is_mystery: bool
    risk_ctrl_info: JsonValue | None = None
    origin_info: GuardUserOriginInfo
    official_info: GuardUserOfficialInfo
    name_color_str: str


class GuardUserMedalInfo(ResponseModel):
    name: str
    level: int
    color_start: int
    color_end: int
    color_border: int
    color: int
    id: int
    typ: int
    is_light: int
    ruid: int
    guard_level: int
    score: int
    guard_icon: str
    honor_icon: str
    v2_medal_color_start: str
    v2_medal_color_end: str
    v2_medal_color_border: str
    v2_medal_color_text: str
    v2_medal_color_level: str
    user_receive_count: int


class GuardUserGuardInfo(ResponseModel):
    level: int
    expired_str: str


class GuardUserInfo(ResponseModel):
    uid: int
    base: GuardUserBaseInfo
    medal: GuardUserMedalInfo
    wealth: JsonValue | None = None
    title: JsonValue | None = None
    guard: GuardUserGuardInfo
    uhead_frame: JsonValue | None = None
    guard_leader: JsonValue | None = None


class GuardMember(ResponseModel):
    ruid: int
    rank: int
    accompany: int
    uinfo: GuardUserInfo
    score: int


class GuardListData(ResponseModel):
    info: GuardTabInfo
    top3: list[GuardMember]
    list: list[GuardMember]


class SilentUserInfo(ResponseModel):
    tuid: int
    tname: str
    uid: int
    name: str
    ctime: str
    id: int
    is_anchor: int
    face: str
    msg: str
    admin_level: int
    is_mystery: bool
    block_end_time: str
    type_name: int = Field(alias="type")


class SilentUserListData(ResponseModel):
    data: list[SilentUserInfo] = Field(default_factory=list)
    total: int
    total_page: int = 0
    pn: int = 0
    ps: int = 0

    @field_validator("data", mode="before")
    @classmethod
    def null_data_is_empty(cls, value: object) -> object:
        return [] if value is None else value


class BannedUserInfo(ResponseModel):
    uid: int
    mtime: str
    face: str
    name: str
    is_anchor: bool
    operator_name: str
    admin_level: int
    is_mystery: bool


class BannedUserListData(ResponseModel):
    data: list[BannedUserInfo] = Field(default_factory=list)
    total: int
    total_page: int = 0
    pn: int = 0
    ps: int = 0

    @field_validator("data", mode="before")
    @classmethod
    def null_data_is_empty(cls, value: object) -> object:
        return [] if value is None else value


class ShieldKeywordInfo(ResponseModel):
    keyword: str
    uid: int
    name: str
    is_anchor: int


class ShieldKeywordListData(ResponseModel):
    keyword_list: list[ShieldKeywordInfo] = Field(default_factory=list)
    max_limit: int

    @field_validator("keyword_list", mode="before")
    @classmethod
    def null_keywords_are_empty(cls, value: object) -> object:
        return [] if value is None else value


class HeartBeatData(ResponseModel):
    next_interval: int


class SendDanmuData(ResponseModel):
    mode_info: JsonValue | None
    dm_v2: JsonValue | None


class CreateRoomData(ResponseModel):
    room_id: str | None = Field(alias="roomID")


class AuditInfo(ResponseModel):
    audit_title_reason: str
    audit_title_status: int
    audit_title: str | None
    update_title: str | None


class UpdateRoomData(ResponseModel):
    sub_session_key: str
    audit_info: AuditInfo | None


class RtmpInfo(ResponseModel):
    addr: str
    code: str


class WebUpStreamAddrData(ResponseModel):
    addr: RtmpInfo
    line: JsonValue
    srt_addr: JsonValue | None = None


class StartLiveData(ResponseModel):
    change: int
    status: str
    rtmp: RtmpInfo | None = None
    live_key: str
    sub_session_key: str
    need_face_auth: bool
    room_type: JsonValue
    protocols: JsonValue
    notice: JsonValue
    qr: JsonValue
    service_source: str
    rtmp_backup: JsonValue
    up_stream_extra: JsonValue


class StopLiveData(ResponseModel):
    change: int
    status: str


class UpdatePreLiveInfoData(ResponseModel):
    audit_info: AuditInfo | None
