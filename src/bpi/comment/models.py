from __future__ import annotations

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel


class CommentData(ResponseModel):
    rpid: int
    rpid_str: str
    root: int
    root_str: str
    parent: int
    parent_str: str
    dialog: int
    dialog_str: str
    success_toast: str | None = None


class CommentPageInfo(ResponseModel):
    num: int
    size: int
    count: int
    acount: int | None = None


class CommentVip(ResponseModel):
    vip_type: int = Field(alias="vipType")
    vip_due_date: int = Field(alias="vipDueDate")
    due_remark: str = Field(alias="dueRemark")
    access_status: int = Field(alias="accessStatus")
    vip_status: int = Field(alias="vipStatus")
    vip_status_warn: str = Field(alias="vipStatusWarn")
    theme_type: int = Field(alias="themeType")
    avatar_subscript: int
    nickname_color: str


class CommentLevelInfo(ResponseModel):
    current_level: int
    current_min: int
    current_exp: int
    next_exp: int


class CommentPendant(ResponseModel):
    pid: int
    name: str
    image: str
    expire: int
    image_enhance: str
    image_enhance_frame: str
    n_pid: int


class CommentNameplate(ResponseModel):
    nid: int
    name: str
    image: str
    image_small: str
    level: str
    condition: str


class CommentOfficialVerify(ResponseModel):
    type: int
    desc: str


class FansDetail(ResponseModel):
    uid: int
    medal_id: int
    medal_name: str
    score: int | None = None
    level: int
    intimacy: int | None = None
    master_status: int | None = None
    is_receive: int | None = None


class JumpUrl(ResponseModel):
    title: str | None = None
    state: int | None = None
    prefix_icon: str | None = None
    app_url_schema: str | None = None
    app_name: str | None = None
    app_package_name: str | None = None
    click_report: str | None = None


class CommentMember(ResponseModel):
    mid: str
    uname: str
    sex: str
    sign: str
    avatar: str
    level_info: CommentLevelInfo
    pendant: CommentPendant
    nameplate: CommentNameplate
    official_verify: CommentOfficialVerify
    vip: CommentVip
    user_sailing: JsonValue = None
    is_contractor: bool = False
    contract_desc: str = ""
    rank: str | None = None
    display_rank: str | None = None
    fans_detail: FansDetail | None = None
    following: int | None = None
    is_followed: int | None = None
    face_nft_new: int | None = None
    senior: JumpUrl | None = None
    user_sailing_v2: JumpUrl | None = None
    nft_interaction: JsonValue | None = None
    avatar_item: JsonValue | None = None


class EmoteMeta(ResponseModel):
    size: int | None = None
    alias: str | None = None


class Emote(ResponseModel):
    id: int
    package_id: int
    state: int
    type: int
    attr: int | None = None
    text: str
    url: str
    meta: EmoteMeta | None = None
    mtime: int | None = None
    jump_title: str | None = None


class Picture(ResponseModel):
    img_src: str
    img_width: int | None = None
    img_height: int | None = None
    img_size: float | None = None


class CommentContent(ResponseModel):
    message: str
    members: list[CommentMember] | None = None
    jump_url: dict[str, JumpUrl] | None = None
    max_line: int | None = None
    plat: int | None = None
    device: str | None = None
    emote: dict[str, Emote] | None = None
    pictures: list[Picture] | None = None


class CommentFolder(ResponseModel):
    has_folded: bool
    is_folded: bool
    rule: str


class UpAction(ResponseModel):
    like: bool
    reply: bool


class CardLabel(ResponseModel):
    rpid: int
    text_content: str
    text_color_day: str
    text_color_night: str
    label_color_day: str
    label_color_night: str
    image: str | None = None
    type: int | None = None
    background: str | None = None
    background_width: int | None = None
    background_height: int | None = None
    jump_url: str | None = None
    effect: int | None = None
    effect_start_time: int | None = None


class ReplyControl(ResponseModel):
    sub_reply_entry_text: str | None = None
    sub_reply_title_text: str | None = None
    time_desc: str | None = None
    location: str | None = None


class Comment(ResponseModel):
    rpid: int
    oid: int
    oid_type: int = Field(alias="type")
    mid: int
    root: int
    parent: int
    dialog: int
    count: int
    rcount: int
    state: int
    fansgrade: int
    attr: int
    ctime: int
    like: int
    action: int
    member: CommentMember
    content: CommentContent
    up_action: UpAction
    invisible: bool
    reply_control: ReplyControl
    folder: CommentFolder
    floor: int | None = None
    show_follow: bool | None = None
    card_label: list[CardLabel] | None = None
    rpid_str: str | None = None
    root_str: str | None = None
    parent_str: str | None = None
    dialog_str: str | None = None
    mid_str: str | None = None
    oid_str: str | None = None
    replies: list[Comment] | None = None
    assist: int | None = None
    dynamic_id_str: str | None = None
    note_cvid_str: str | None = None
    track_info: str | None = None


class CommentTop(ResponseModel):
    admin: JsonValue
    upper: JsonValue
    vote: JsonValue


class CommentConfig(ResponseModel):
    showtopic: int
    show_up_flag: bool
    read_only: bool


class CommentCursor(ResponseModel):
    is_begin: bool
    prev: int
    next: int
    is_end: bool
    pagination_reply: JsonValue
    session_id: str
    mode: int
    mode_text: str
    all_count: int | None = None
    support_mode: list[int] | None = None


class CommentUpper(ResponseModel):
    mid: int


class CommentControl(ResponseModel):
    input_disable: bool
    root_input_text: str
    child_input_text: str
    giveup_input_text: str
    screenshot_icon_state: int
    upload_picture_icon_state: int
    answer_guide_text: str
    answer_guide_icon_url: str
    answer_guide_ios_url: str
    answer_guide_android_url: str
    bg_text: str
    empty_page: JsonValue | None = None
    show_type: int
    show_text: str
    web_selection: bool
    disable_jump_emote: bool
    enable_charged: bool
    enable_cm_biz_helper: bool
    preload_resources: JsonValue | None = None


class CommentAdInfo(ResponseModel):
    id: int
    contract_id: str
    pos_num: int
    name: str
    pic: str
    litpic: str
    url: str
    style: int
    agency: str
    label: str
    intro: str
    creative_type: int
    request_id: str
    src_id: int
    area: int
    is_ad_loc: bool
    ad_cb: str
    title: str
    server_type: int
    cm_mark: int
    stime: int
    mid: str
    activity_type: int
    epid: int
    sub_title: str
    ad_desc: str
    adver_name: str
    null_frame: bool
    pic_main_color: str


class CommentListData(ResponseModel):
    page: CommentPageInfo | None = None
    cursor: CommentCursor | None = None
    replies: list[Comment] | None = None
    top: CommentTop | None = None
    top_replies: list[Comment] | None = None
    effects: JsonValue | None = None
    assist: int | None = None
    blacklist: int | None = None
    vote: int | None = None
    config: CommentConfig | None = None
    upper: CommentUpper | None = None
    control: CommentControl | None = None
    note: int | None = None
    cm_info: CommentAdInfo | None = None


class HotCommentData(ResponseModel):
    page: CommentPageInfo
    replies: list[Comment]


class CountData(ResponseModel):
    count: int
