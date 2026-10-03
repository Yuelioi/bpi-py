from __future__ import annotations

from typing import Annotated

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel


class UnreadCountData(ResponseModel):
    coin: int
    danmu: int = 0
    favorite: int
    recv_like: int
    recv_reply: int
    sys_msg: int
    up: int


class ReplyCursor(ResponseModel):
    is_end: bool
    id: int | None = None
    time: int | None = None


class ReplyUser(ResponseModel):
    mid: int
    nickname: str
    avatar: str
    follow: bool
    fans: int | None = None
    mid_link: str | None = None


class AtUserDetail(ResponseModel):
    mid: int
    nickname: str
    avatar: str
    follow: bool


class ReplyDetail(ResponseModel):
    subject_id: int
    root_id: int
    source_id: int
    target_id: int
    reply_type: str = Field(alias="type")
    business_id: int
    business: str
    title: str
    desc: str
    uri: str
    native_uri: str
    root_reply_content: str
    source_content: str
    target_reply_content: str
    at_details: list[AtUserDetail]
    hide_reply_button: bool
    hide_like_button: bool
    like_state: int


class ReplyItem(ResponseModel):
    id: int
    user: ReplyUser
    item: ReplyDetail
    counts: int
    is_multi: int
    reply_time: int


class ReplyFeedData(ResponseModel):
    cursor: ReplyCursor
    items: list[ReplyItem]
    last_view_at: int


class SingleUnreadData(ResponseModel):
    unfollow_unread: int
    follow_unread: int
    unfollow_push_msg: int
    dustbin_push_msg: int
    dustbin_unread: int
    biz_msg_unfollow_unread: int
    biz_msg_follow_unread: int
    custom_unread: int


class EmojiInfo(ResponseModel):
    text: str
    uri: str
    size: int
    gif_url: str | None = None


class KeyHitInfos(ResponseModel):
    toast: str | None = None
    rule_id: int | None = None
    high_text: list[JsonValue] | None = None


class SendMsgData(ResponseModel):
    msg_key: int | None = None
    e_infos: list[EmojiInfo] | None = None
    msg_content: str | None = None
    key_hit_infos: KeyHitInfos | None = None


class MessageImage(ResponseModel):
    url: str
    height: int
    width: int
    image_type: str | None = Field(default=None, alias="imageType")
    original: int | None = None
    size: float


UInt64 = Annotated[int, Field(ge=0, le=2**64 - 1)]
UInt32 = Annotated[int, Field(ge=0, le=2**32 - 1)]


class PrivateMessage(ResponseModel):
    """content 保留嵌套 JSON 字符串，未知消息类型不丢弃。"""

    sender_uid: UInt64
    receiver_id: UInt64
    receiver_type: UInt32
    msg_type: UInt32
    content: str
    msg_seqno: UInt64
    msg_key: UInt64
    timestamp: UInt64
    msg_status: UInt32
    msg_source: UInt32
    at_uids: list[UInt64] | None = None
    new_face_version: UInt32 | None = None
    notify_code: str


class Session(ResponseModel):
    talker_id: UInt64
    session_type: UInt32
    session_ts: UInt64
    top_ts: UInt64
    ack_seqno: UInt64
    ack_ts: UInt64
    max_seqno: UInt64
    unread_count: UInt32
    system_msg_type: UInt32
    is_follow: UInt32
    is_dnd: UInt32
    last_msg: PrivateMessage


class SessionsData(ResponseModel):
    session_list: list[Session] | None = None
    has_more: UInt32
    is_address_list_empty: UInt32
    anti_disturb_cleaning: bool
    show_level: bool


class SessionMessagesData(ResponseModel):
    messages: list[PrivateMessage] | None = None
    has_more: UInt32
    min_seqno: UInt64
    max_seqno: UInt64
