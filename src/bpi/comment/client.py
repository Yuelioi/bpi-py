from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from .models import CommentData, CommentListData, CountData, HotCommentData
from .params import (
    CommentSort,
    CommentType,
    ReportReason,
    action_form,
    add_form,
    delete_form,
    list_query,
    replies_query,
    report_form,
    target_query,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_COMMENT = TypeAdapter(CommentData)
_LIST = TypeAdapter(CommentListData)
_HOT: TypeAdapter[HotCommentData | None] = TypeAdapter(HotCommentData | None)
_COUNT = TypeAdapter(CountData)
_OPTIONAL_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class CommentClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        comment_type: int,
        oid: int,
        page: int | None = None,
        page_size: int | None = None,
        sort: CommentSort | int | None = None,
        nohot: bool | None = None,
    ) -> CommentListData:
        params = list_query(
            comment_type, oid, page=page, page_size=page_size, sort=sort, nohot=nohot
        )
        return await self._client._get_payload("/x/v2/reply", params, _LIST)

    async def replies(
        self,
        *,
        comment_type: int,
        oid: int,
        root: int,
        page: int | None = None,
        page_size: int | None = None,
    ) -> CommentListData:
        params = replies_query(comment_type, oid, root, page=page, page_size=page_size)
        return await self._client._get_payload("/x/v2/reply/reply", params, _LIST)

    async def hot(
        self,
        *,
        comment_type: int,
        oid: int,
        root: int,
        page: int | None = None,
        page_size: int | None = None,
    ) -> HotCommentData | None:
        params = replies_query(comment_type, oid, root, page=page, page_size=page_size)
        return await self._client._get_payload("/x/v2/reply/hot", params, _HOT, optional=True)

    async def count(self, *, comment_type: int, oid: int) -> CountData:
        return await self._client._get_payload(
            "/x/v2/reply/count", target_query(comment_type, oid), _COUNT
        )

    async def add(
        self,
        *,
        comment_type: CommentType | int,
        oid: int,
        message: str,
        root: int | None = None,
        parent: int | None = None,
    ) -> CommentData:
        form = add_form(comment_type, oid, message, root=root, parent=parent)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload("/x/v2/reply/add", {}, _COMMENT, form=form)

    async def like(
        self, *, comment_type: CommentType | int, oid: int, rpid: int, action: int
    ) -> JsonValue:
        return await self._action("/x/v2/reply/action", comment_type, oid, rpid, action)

    async def dislike(
        self, *, comment_type: CommentType | int, oid: int, rpid: int, action: int
    ) -> JsonValue:
        return await self._action("/x/v2/reply/hate", comment_type, oid, rpid, action)

    async def top(
        self, *, comment_type: CommentType | int, oid: int, rpid: int, action: int
    ) -> JsonValue:
        return await self._action("/x/v2/reply/top", comment_type, oid, rpid, action)

    async def _action(
        self, path: str, comment_type: CommentType | int, oid: int, rpid: int, action: int
    ) -> JsonValue:
        form = action_form(comment_type, oid, rpid, action)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(path, {}, _OPTIONAL_JSON, form=form, optional=True)

    async def delete(self, *, comment_type: CommentType | int, oid: int, rpid: int) -> JsonValue:
        form = delete_form(comment_type, oid, rpid)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/v2/reply/del", {}, _OPTIONAL_JSON, form=form, optional=True
        )

    async def report(
        self,
        *,
        comment_type: CommentType | int,
        oid: int,
        rpid: int,
        reason: ReportReason | int,
        content: str | None = None,
    ) -> JsonValue:
        form = report_form(comment_type, oid, rpid, reason, content=content)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/v2/reply/report", {}, _OPTIONAL_JSON, form=form, optional=True
        )
