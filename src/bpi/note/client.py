from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from .models import (
    NoteAddResponseData,
    NoteIsForbidData,
    NoteListArchiveData,
    PrivateNoteInfoData,
    PrivateNoteListData,
    PublicNoteInfoData,
    PublicNoteListArchiveData,
    PublicNoteListUserData,
)
from .params import (
    add_form,
    archive_query,
    delete_form,
    is_forbid_query,
    pagination,
    private_info_query,
    public_archive_query,
    public_info_query,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_IS_FORBID = TypeAdapter(NoteIsForbidData)
_PRIVATE_INFO = TypeAdapter(PrivateNoteInfoData)
_PUBLIC_INFO = TypeAdapter(PublicNoteInfoData)
_ARCHIVE_LIST = TypeAdapter(NoteListArchiveData)
_PRIVATE_LIST = TypeAdapter(PrivateNoteListData)
_PUBLIC_ARCHIVE_LIST = TypeAdapter(PublicNoteListArchiveData)
_PUBLIC_USER_LIST = TypeAdapter(PublicNoteListUserData)
_ADD = TypeAdapter(NoteAddResponseData)
_OPTIONAL_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class NoteClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def is_forbid(self, *, aid: int) -> NoteIsForbidData:
        return await self._client._get_payload(
            "/x/note/is_forbid", is_forbid_query(aid), _IS_FORBID
        )

    async def private_info(self, *, aid: int, note_id: int) -> PrivateNoteInfoData:
        return await self._client._get_payload(
            "/x/note/info", private_info_query(aid, note_id), _PRIVATE_INFO
        )

    async def public_info(self, *, cvid: int) -> PublicNoteInfoData:
        return await self._client._get_payload(
            "/x/note/publish/info", public_info_query(cvid), _PUBLIC_INFO
        )

    async def archive_list(self, *, aid: int) -> NoteListArchiveData:
        return await self._client._get_payload(
            "/x/note/list/archive", archive_query(aid), _ARCHIVE_LIST
        )

    async def user_private_list(self, *, page: int = 1, page_size: int = 10) -> PrivateNoteListData:
        return await self._client._get_payload(
            "/x/note/list", pagination(page, page_size), _PRIVATE_LIST
        )

    async def public_archive_list(
        self, *, aid: int, page: int = 1, page_size: int = 10
    ) -> PublicNoteListArchiveData:
        return await self._client._get_payload(
            "/x/note/publish/list/archive",
            public_archive_query(aid, page, page_size),
            _PUBLIC_ARCHIVE_LIST,
        )

    async def user_public_list(
        self, *, page: int = 1, page_size: int = 10
    ) -> PublicNoteListUserData:
        return await self._client._get_payload(
            "/x/note/publish/list/user", pagination(page, page_size), _PUBLIC_USER_LIST
        )

    async def add(
        self,
        *,
        aid: int,
        title: str,
        summary: str,
        content: str,
        note_id: str | None = None,
        tags: str | None = None,
        publish: bool | None = None,
        auto_comment: bool | None = None,
    ) -> NoteAddResponseData:
        form = add_form(
            aid,
            title,
            summary,
            content,
            note_id=note_id,
            tags=tags,
            publish=publish,
            auto_comment=auto_comment,
        )
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload("/x/note/add", {}, _ADD, form=form)

    async def delete(self, *, aid: int, note_id: str | None = None) -> JsonValue:
        form = delete_form(aid, note_id)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/note/del", {}, _OPTIONAL_JSON, form=form, optional=True
        )
