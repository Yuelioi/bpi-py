from __future__ import annotations

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
