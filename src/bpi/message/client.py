from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import uuid4

from pydantic import TypeAdapter

from bpi.errors import AuthenticationError, InvalidParameterError
from bpi.session import parse_cookie

from .models import (
    MessageImage,
    ReplyFeedData,
    SendMsgData,
    SessionMessagesData,
    SessionsData,
    SingleUnreadData,
    UnreadCountData,
)
from .params import (
    SessionListType,
    SingleUnreadType,
    receiver_query,
    reply_feed_query,
    session_messages_query,
    sessions_query,
    single_unread_query,
    unread_count_query,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_UNREAD = TypeAdapter(UnreadCountData)
_REPLY = TypeAdapter(ReplyFeedData)
_SINGLE = TypeAdapter(SingleUnreadData)
_SEND = TypeAdapter(SendMsgData)
_SESSIONS = TypeAdapter(SessionsData)
_SESSION_MESSAGES = TypeAdapter(SessionMessagesData)


class MessageClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def sessions(
        self,
        *,
        session_type: int | SessionListType = SessionListType.ALL,
        size: int = 100,
        begin_ts: int | None = None,
        end_ts: int | None = None,
    ) -> SessionsData:
        """读取一页会话，不标记已读。ALL 可能忽略 end_ts，须检查游标前进。"""
        return await self._client._get_payload(
            "/session_svr/v1/session_svr/get_sessions",
            sessions_query(session_type, size, begin_ts, end_ts),
            _SESSIONS,
            host="api.vc.bilibili.com",
        )

    async def session_messages(
        self,
        *,
        talker_id: int,
        size: int = 100,
        begin_seqno: int | None = None,
        end_seqno: int | None = None,
    ) -> SessionMessagesData:
        """读取一页用户私信，保留服务端顺序和序列号边界。"""
        return await self._client._get_payload(
            "/svr_sync/v1/svr_sync/fetch_session_msgs",
            session_messages_query(talker_id, size, begin_seqno, end_seqno),
            _SESSION_MESSAGES,
            host="api.vc.bilibili.com",
        )

    async def unread_count(self, *, build: str = "0", mobi_app: str = "web") -> UnreadCountData:
        return await self._client._get_payload(
            "/x/im/web/msgfeed/unread",
            unread_count_query(build, mobi_app),
            _UNREAD,
            host="api.vc.bilibili.com",
        )

    async def reply_feed(
        self,
        *,
        start_id: int | None = None,
        start_time: int | None = None,
        web_location: str = "",
    ) -> ReplyFeedData:
        return await self._client._get_payload(
            "/x/msgfeed/reply",
            reply_feed_query(start_id, start_time, web_location),
            _REPLY,
        )

    async def single_unread(
        self,
        *,
        unread_type: int | SingleUnreadType = SingleUnreadType.ALL,
        show_unfollow_list: bool = False,
        show_dustbin: bool | None = None,
    ) -> SingleUnreadData:
        return await self._client._get_payload(
            "/session_svr/v1/session_svr/single_unread",
            single_unread_query(unread_type, show_unfollow_list, show_dustbin),
            _SINGLE,
            host="api.vc.bilibili.com",
        )

    async def send(
        self,
        *,
        receiver_id: int,
        message: str | MessageImage,
        receiver_type: int = 1,
    ) -> SendMsgData:
        """发送私信，需要账号、CSRF 与 WBI；失败不自动重试，须核对非零 msg_key。"""
        receiver, receiver_kind = receiver_query(receiver_id, receiver_type)
        if isinstance(message, str):
            if not message.strip():
                raise InvalidParameterError("text cannot be blank")
            msg_type = "1"
            content = json.dumps({"content": message}, ensure_ascii=False, separators=(",", ":"))
            try:
                encoded_size = len(content.encode("utf-8"))
            except UnicodeError:
                raise InvalidParameterError("text must be valid UTF-8") from None
            if encoded_size > 2000:
                raise InvalidParameterError("encoded text exceeds 2000 bytes")
        elif isinstance(message, MessageImage):
            msg_type = "2"
            content = message.model_dump_json(by_alias=True)
        else:
            raise InvalidParameterError("message must be text or MessageImage")

        csrf = self._client.csrf()
        cookie_request = self._client._http.build_request("GET", "https://api.bilibili.com/")
        sender_uid = parse_cookie(cookie_request.headers.get("cookie", "")).get("DedeUserID")
        if not sender_uid:
            raise AuthenticationError(-101)
        dev_id = str(uuid4())
        timestamp = int(self._client._clock())

        form = {
            "msg[sender_uid]": sender_uid,
            "msg[receiver_id]": receiver,
            "msg[receiver_type]": receiver_kind,
            "msg[msg_type]": msg_type,
            "msg[msg_status]": "0",
            "msg[dev_id]": dev_id,
            "msg[timestamp]": str(timestamp),
            "msg[new_face_version]": "1",
            "csrf": csrf,
            "csrf_token": csrf,
            "build": "0",
            "mobi_app": "web",
            "msg[content]": content,
        }
        signed = await self._client._sign(
            {"w_sender_uid": sender_uid, "w_receiver_id": receiver, "w_dev_id": dev_id}
        )
        return await self._client._post_payload(
            "/web_im/v1/web_im/send_msg",
            signed,
            _SEND,
            form=form,
            host="api.vc.bilibili.com",
        )
