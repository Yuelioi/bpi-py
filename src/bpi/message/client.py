from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import uuid4

from pydantic import TypeAdapter

from bpi.errors import AuthenticationError, InvalidParameterError
from bpi.session import parse_cookie

from .models import MessageImage, ReplyFeedData, SendMsgData, SingleUnreadData, UnreadCountData
from .params import (
    SingleUnreadType,
    receiver_query,
    reply_feed_query,
    single_unread_query,
    unread_count_query,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_UNREAD = TypeAdapter(UnreadCountData)
_REPLY = TypeAdapter(ReplyFeedData)
_SINGLE = TypeAdapter(SingleUnreadData)
_SEND = TypeAdapter(SendMsgData)


class MessageClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

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
        receiver, receiver_kind = receiver_query(receiver_id, receiver_type)
        csrf = self._client.csrf()
        cookie_request = self._client._http.build_request("GET", "https://api.bilibili.com/")
        sender_uid = parse_cookie(cookie_request.headers.get("cookie", "")).get("DedeUserID")
        if not sender_uid:
            raise AuthenticationError(-101)

        dev_id = str(uuid4())
        timestamp = int(self._client._clock())
        if isinstance(message, str):
            msg_type = "1"
            content = json.dumps({"content": message}, ensure_ascii=False, separators=(",", ":"))
        elif isinstance(message, MessageImage):
            msg_type = "2"
            content = message.model_dump_json(by_alias=True)
        else:
            raise InvalidParameterError("message must be text or MessageImage")

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
