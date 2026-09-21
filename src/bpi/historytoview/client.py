from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue, StrictBool, TypeAdapter

from .models import HistoryListData, ToViewListData
from .params import (
    HistoryBusiness,
    HistoryListType,
    history_delete_form,
    history_list_query,
    history_shadow_form,
    toview_add_form,
    toview_delete_form,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient

_HISTORY_LIST = TypeAdapter(HistoryListData)
_BOOL = TypeAdapter(StrictBool)
_TOVIEW_LIST = TypeAdapter(ToViewListData)
_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class HistoryToViewClient:
    """Account history and watch-later API entry point."""

    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def history_list(
        self,
        *,
        max_id: int | None = None,
        business: HistoryBusiness | str | None = None,
        view_at: int | None = None,
        list_type: HistoryListType | str | None = None,
        page_size: int | None = None,
    ) -> HistoryListData:
        params = history_list_query(max_id, business, view_at, list_type, page_size)
        return await self._client._get_payload(
            "/x/web-interface/history/cursor", params, _HISTORY_LIST
        )

    async def history_shadow(self) -> bool:
        return await self._client._get_payload("/x/v2/history/shadow", {}, _BOOL)

    async def toview_list(self) -> ToViewListData:
        return await self._client._get_payload("/x/v2/history/toview", {}, _TOVIEW_LIST)

    async def delete_history(self, *, kid: str) -> JsonValue:
        form = history_delete_form(kid, self._client.csrf())
        return await self._client._post_payload(
            "/x/v2/history/delete", {}, _JSON, form=form, optional=True
        )

    async def clear_history(self) -> JsonValue:
        return await self._client._post_payload(
            "/x/v2/history/clear",
            {},
            _JSON,
            form={"csrf": self._client.csrf()},
            optional=True,
        )

    async def set_history_shadow(self, *, switch: bool) -> JsonValue:
        form = history_shadow_form(switch, self._client.csrf())
        return await self._client._post_payload(
            "/x/v2/history/shadow/set", {}, _JSON, form=form, optional=True
        )

    async def add_toview(
        self, *, aid: int | None = None, bvid: str | None = None
    ) -> JsonValue:
        form = toview_add_form(aid, bvid, self._client.csrf())
        return await self._client._post_payload(
            "/x/v2/history/toview/add", {}, _JSON, form=form, optional=True
        )

    async def delete_toview(
        self, *, aid: int | None = None, viewed: bool | None = None
    ) -> JsonValue:
        form = toview_delete_form(aid, viewed, self._client.csrf())
        return await self._client._post_payload(
            "/x/v2/history/toview/del", {}, _JSON, form=form, optional=True
        )

    async def clear_toview(self) -> JsonValue:
        return await self._client._post_payload(
            "/x/v2/history/toview/clear",
            {},
            _JSON,
            form={"csrf": self._client.csrf()},
            optional=True,
        )
