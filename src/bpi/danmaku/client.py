from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from .models import (
    DanmakuAdvState,
    DanmakuPostData,
    DanmakuXml,
    ThumbupStatsItem,
    parse_deflate_danmaku_xml,
)
from .params import (
    adv_state_query,
    buy_adv_form,
    edit_pool_form,
    edit_state_form,
    history_bytes_query,
    history_dates_query,
    recall_form,
    report_form,
    segment_query,
    send_form,
    snapshot_query,
    thumbup_form,
    thumbup_stats_query,
    web_view_query,
    xml_list_query,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_OPTIONAL_STRINGS: TypeAdapter[list[str] | None] = TypeAdapter(list[str] | None)
_STRINGS = TypeAdapter(list[str])
_THUMBUP_STATS = TypeAdapter(dict[str, ThumbupStatsItem])
_ADV_STATE = TypeAdapter(DanmakuAdvState)
_POST = TypeAdapter(DanmakuPostData)
_OPTIONAL_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class DanmakuClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def history_dates(
        self, *, oid: int, month: str, danmaku_type: int = 1
    ) -> list[str] | None:
        return await self._client._get_payload(
            "/x/v2/dm/history/index",
            history_dates_query(oid, month, danmaku_type=danmaku_type),
            _OPTIONAL_STRINGS,
            optional=True,
        )

    async def snapshot(self, *, aid: int | None = None, bvid: str | None = None) -> list[str]:
        return await self._client._get_payload(
            "/x/v2/dm/ajax", snapshot_query(aid=aid, bvid=bvid), _STRINGS
        )

    async def thumbup_stats(self, *, oid: int, ids: Iterable[int]) -> dict[str, ThumbupStatsItem]:
        return await self._client._get_payload(
            "/x/v2/dm/thumbup/stats", thumbup_stats_query(oid, ids), _THUMBUP_STATS
        )

    async def adv_state(self, *, cid: int) -> DanmakuAdvState:
        return await self._client._get_payload("/x/dm/adv/state", adv_state_query(cid), _ADV_STATE)

    async def web_seg_proto(
        self,
        *,
        danmaku_type: int,
        oid: int,
        segment_index: int,
        pid: int | None = None,
        pull_mode: int | None = None,
        ps: int | None = None,
        pe: int | None = None,
    ) -> bytes:
        params = segment_query(
            danmaku_type, oid, segment_index, pid=pid, pull_mode=pull_mode, ps=ps, pe=pe
        )
        return await self._client._get("/x/v2/dm/web/seg.so", params)

    async def web_seg_wbi_proto(
        self,
        *,
        danmaku_type: int,
        oid: int,
        segment_index: int,
        pid: int | None = None,
        pull_mode: int | None = None,
        ps: int | None = None,
        pe: int | None = None,
    ) -> bytes:
        params = segment_query(
            danmaku_type, oid, segment_index, pid=pid, pull_mode=pull_mode, ps=ps, pe=pe
        )
        signed = await self._client._sign(params)
        return await self._client._get("/x/v2/dm/wbi/web/seg.so", signed)

    async def web_view_proto(self, *, danmaku_type: int, oid: int, pid: int | None = None) -> bytes:
        return await self._client._get(
            "/x/v2/dm/web/view", web_view_query(danmaku_type, oid, pid=pid)
        )

    async def mobile_seg_proto(
        self,
        *,
        danmaku_type: int,
        oid: int,
        segment_index: int,
        pid: int | None = None,
        pull_mode: int | None = None,
        ps: int | None = None,
        pe: int | None = None,
    ) -> bytes:
        params = segment_query(
            danmaku_type, oid, segment_index, pid=pid, pull_mode=pull_mode, ps=ps, pe=pe
        )
        return await self._client._get("/x/v2/dm/list/seg.so", params)

    async def web_history_seg_proto(self, *, danmaku_type: int, oid: int, date: str) -> bytes:
        return await self._client._get(
            "/x/v2/dm/web/history/seg.so", history_bytes_query(danmaku_type, oid, date)
        )

    async def history_xml_bytes(self, *, danmaku_type: int, oid: int, date: str) -> bytes:
        return await self._client._get_raw(
            "/x/v2/dm/history", history_bytes_query(danmaku_type, oid, date)
        )

    async def xml_list_so(self, *, cid: int) -> DanmakuXml:
        body = await self._client._get_raw("/x/v1/dm/list.so", xml_list_query(cid))
        return parse_deflate_danmaku_xml(body)

    async def xml_list(self, *, cid: int) -> DanmakuXml:
        xml_list_query(cid)
        body = await self._client._get_raw(f"/{cid}.xml", {}, host="comment.bilibili.com")
        return parse_deflate_danmaku_xml(body)

    async def send(
        self,
        *,
        oid: int,
        msg: str,
        aid: int | None = None,
        bvid: str | None = None,
        mode: int = 1,
        danmaku_type: int = 1,
        progress: int = 1878,
        color: int = 16_777_215,
        font_size: int = 25,
        pool: int = 0,
    ) -> DanmakuPostData:
        form = send_form(
            oid,
            msg,
            aid=aid,
            bvid=bvid,
            mode=mode,
            danmaku_type=danmaku_type,
            progress=progress,
            color=color,
            font_size=font_size,
            pool=pool,
        )
        form["csrf"] = self._client.csrf()
        signed = await self._client._sign(form)
        return await self._client._post_payload("/x/v2/dm/post", {}, _POST, form=signed)

    async def recall(self, *, cid: int, dmid: int) -> JsonValue:
        form = recall_form(cid, dmid)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/dm/recall", {}, _OPTIONAL_JSON, form=form, optional=True
        )

    async def buy_adv(self, *, cid: int) -> JsonValue:
        form = buy_adv_form(cid)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/dm/adv/buy", {}, _OPTIONAL_JSON, form=form, optional=True
        )

    async def thumbup(self, *, oid: int, dmid: int, op: int) -> JsonValue:
        form = thumbup_form(oid, dmid, op)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/v2/dm/thumbup/add", {}, _OPTIONAL_JSON, form=form, optional=True
        )

    async def report(
        self, *, cid: int, dmid: int, reason: int, content: str | None = None
    ) -> JsonValue:
        form = report_form(cid, dmid, reason, content=content)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/dm/report/add", {}, _OPTIONAL_JSON, form=form, optional=True
        )

    async def edit_state(self, *, oid: int, dmids: Iterable[int], state: int) -> JsonValue:
        form = edit_state_form(oid, dmids, state)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/v2/dm/edit/state", {}, _OPTIONAL_JSON, form=form, optional=True
        )

    async def edit_pool(self, *, oid: int, dmids: Iterable[int], pool: int) -> JsonValue:
        form = edit_pool_form(oid, dmids, pool)
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/v2/dm/edit/pool", {}, _OPTIONAL_JSON, form=form, optional=True
        )
