from __future__ import annotations

import builtins

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel


class NoteIsForbidData(ResponseModel):
    forbid_note_entrance: bool


class PrivateNoteArc(ResponseModel):
    oid: int
    oid_type: int
    title: str
    pic: str
    status: int
    desc: str


class PrivateNoteTag(ResponseModel):
    cid: int
    status: int
    index: int
    seconds: int
    pos: int


class PrivateNoteInfoData(ResponseModel):
    arc: PrivateNoteArc
    audit_status: int
    cid_count: int
    content: str
    forbid_note_entrance: bool
    pub_reason: str | None = None
    pub_status: int
    pub_version: int
    summary: str
    tags: builtins.list[PrivateNoteTag]
    title: str


class PublicNoteArc(ResponseModel):
    oid: int
    oid_type: int
    title: str
    status: int
    pic: str
    desc: str


class PublicNoteAuthor(ResponseModel):
    mid: int
    name: str
    face: str
    level: int
    vip_info: JsonValue
    pendant: JsonValue


class PublicNoteInfoData(ResponseModel):
    cvid: int
    note_id: int
    title: str
    summary: str
    content: str
    cid_count: int
    pub_status: int
    tags: builtins.list[PrivateNoteTag]
    arc: PublicNoteArc
    author: PublicNoteAuthor
    forbid_note_entrance: bool


class NoteListArchiveData(ResponseModel):
    note_ids: builtins.list[str] | None = Field(default=None, alias="noteIds")


class PrivateNoteListArc(ResponseModel):
    oid: int
    status: int
    oid_type: int
    aid: int
    bvid: str | None = None
    pic: str | None = None
    desc: str | None = None


class PrivateNoteItem(ResponseModel):
    title: str
    summary: str
    mtime: str
    arc: PrivateNoteListArc
    note_id: int
    audit_status: int
    web_url: str
    note_id_str: str
    message: str
    forbid_note_entrance: bool | None = None
    likes: int
    has_like: bool


class NotePage(ResponseModel):
    total: int
    size: int
    num: int


class PrivateNoteListData(ResponseModel):
    list: builtins.list[PrivateNoteItem] | None = None
    page: NotePage | None = None


class PublicNoteItem(ResponseModel):
    cvid: int
    title: str
    summary: str
    pubtime: str
    web_url: str
    message: str
    author: PublicNoteAuthor
    likes: int
    has_like: bool


class PublicNoteListArchiveData(ResponseModel):
    list: builtins.list[PublicNoteItem] | None = None
    page: NotePage | None = None
    show_public_note: bool
    message: str


class PublicNoteListUserData(ResponseModel):
    list: builtins.list[PublicNoteItem] | None = None
    page: NotePage | None = None


class NoteAddResponseData(ResponseModel):
    note_id: str
