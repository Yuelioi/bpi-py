"""Source-derived user relation/group writes; all require explicit CSRF session state."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from bpi._core.params import integer
from bpi._core.response import ResponseModel
from bpi.errors import InvalidParameterError

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


class CreateTagResponseData(ResponseModel):
    tagid: int


_CREATE_TAG = TypeAdapter(CreateTagResponseData)
_OPTIONAL: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_NONE = TypeAdapter(type(None))

_RELATION_ACTIONS = set(range(1, 8))
_RELATION_SOURCES = {
    1,
    11,
    14,
    15,
    17,
    58,
    106,
    107,
    115,
    118,
    120,
    164,
    167,
    192,
    222,
    229,
    235,
    245,
}


def _choice(value: int, name: str, allowed: set[int]) -> str:
    result = integer(value, name)
    if value not in allowed:
        raise InvalidParameterError(f"Unsupported {name}")
    return result


def _name(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidParameterError(f"{field} must be a string")
    result = value.strip()
    if not result:
        raise InvalidParameterError(f"{field} cannot be blank")
    if len(result.encode()) > 16:
        raise InvalidParameterError(f"{field} cannot exceed 16 bytes")
    return result


def _ids(values: Sequence[int], field: str) -> str:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or not values:
        raise InvalidParameterError(f"{field} must be a non-empty sequence of integers")
    if any(type(value) is not int or value <= 0 for value in values):
        raise InvalidParameterError(f"{field} must contain positive integers")
    return ",".join(str(value) for value in values)


class UserActionMethods:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def modify_relation(
        self, *, fid: int, action: int, source: int | None = None
    ) -> None:
        form = {
            "fid": integer(fid, "fid"),
            "act": _choice(action, "action", _RELATION_ACTIONS),
            "csrf": self._client.csrf(),
        }
        if source is not None:
            form["re_src"] = _choice(source, "source", _RELATION_SOURCES)
        return await self._client._post_payload(
            "/x/relation/modify", {}, _NONE, form=form, multipart=True, optional=True
        )

    async def create_group_tag(self, *, group_name: str) -> CreateTagResponseData:
        form = {"tag": _name(group_name, "group_name"), "csrf": self._client.csrf()}
        return await self._client._post_payload(
            "/x/relation/tag/create", {}, _CREATE_TAG, form=form, multipart=True
        )

    async def update_group_tag(self, *, tag_id: int, new_name: str) -> JsonValue:
        form = {
            "tagid": integer(tag_id, "tag_id"),
            "name": _name(new_name, "new_name"),
            "csrf": self._client.csrf(),
        }
        return await self._client._post_payload(
            "/x/relation/tag/update", {}, _OPTIONAL, form=form, multipart=True, optional=True
        )

    async def delete_group_tag(self, *, tag_id: int) -> JsonValue:
        form = {"tagid": integer(tag_id, "tag_id"), "csrf": self._client.csrf()}
        return await self._client._post_payload(
            "/x/relation/tag/del", {}, _OPTIONAL, form=form, multipart=True, optional=True
        )

    async def add_group_users_to_tags(
        self, *, fids: Sequence[int], tag_ids: Sequence[int]
    ) -> JsonValue:
        return await self._group_users(
            "/x/relation/tags/addUsers", fids=fids, tag_ids=tag_ids
        )

    async def remove_group_users(
        self, *, fids: Sequence[int], tag_ids: Sequence[int] | None = None
    ) -> JsonValue:
        return await self._group_users(
            "/x/relation/tags/addUsers", fids=fids, tag_ids=tag_ids, remove_all=tag_ids is None
        )

    async def copy_group_users_to_tags(
        self, *, fids: Sequence[int], tag_ids: Sequence[int]
    ) -> JsonValue:
        return await self._group_users(
            "/x/relation/tags/copyUsers", fids=fids, tag_ids=tag_ids
        )

    async def move_group_users_to_tags(
        self,
        *,
        fids: Sequence[int],
        before_tag_ids: Sequence[int],
        after_tag_ids: Sequence[int],
    ) -> JsonValue:
        form = {
            "fids": _ids(fids, "fids"),
            "beforeTagids": _ids(before_tag_ids, "before_tag_ids"),
            "afterTagids": _ids(after_tag_ids, "after_tag_ids"),
            "csrf": self._client.csrf(),
        }
        return await self._client._post_payload(
            "/x/relation/tags/moveUsers",
            {},
            _OPTIONAL,
            form=form,
            multipart=True,
            optional=True,
        )

    async def set_space_notice(self, *, notice: str | None = None) -> None:
        form = {"csrf": self._client.csrf()}
        if notice is not None:
            if not isinstance(notice, str):
                raise InvalidParameterError("notice must be a string")
            if len(notice.encode()) > 150:
                raise InvalidParameterError("notice cannot exceed 150 bytes")
            form["notice"] = notice
        return await self._client._post_payload(
            "/x/space/notice/set", {}, _NONE, form=form, multipart=True, optional=True
        )

    async def _group_users(
        self,
        path: str,
        *,
        fids: Sequence[int],
        tag_ids: Sequence[int] | None,
        remove_all: bool = False,
    ) -> JsonValue:
        form = {
            "fids": _ids(fids, "fids"),
            "tagids": "0" if remove_all else _ids(tag_ids or (), "tag_ids"),
            "csrf": self._client.csrf(),
        }
        return await self._client._post_payload(
            path, {}, _OPTIONAL, form=form, multipart=True, optional=True
        )
