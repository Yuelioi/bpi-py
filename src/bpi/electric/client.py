from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from .models import (
    BcoinQuickPayData,
    ChargeFollowInfo,
    ChargeMonthUpData,
    ChargeRecordData,
    ElecRankData,
    ElecRemarkDetail,
    ElecRemarkList,
    MemberRankData,
    RechargeData,
    UpowerItemDetail,
    VideoElecShowData,
)
from .params import (
    bcoin_quick_pay_form,
    charge_record_query,
    message_form,
    month_up_list_query,
    rank_recent_query,
    recharge_list_query,
    remark_detail_query,
    remark_list_query,
    reply_remark_form,
    upower_member_rank_query,
    video_show_query,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_MONTH_UP_LIST = TypeAdapter(ChargeMonthUpData)
_VIDEO_SHOW = TypeAdapter(VideoElecShowData)
_RECHARGE_LIST = TypeAdapter(RechargeData)
_RANK_RECENT = TypeAdapter(ElecRankData)
_CHARGE_RECORD = TypeAdapter(ChargeRecordData)
_UPOWER_ITEM_DETAIL = TypeAdapter(UpowerItemDetail)
_CHARGE_FOLLOW_INFO = TypeAdapter(ChargeFollowInfo)
_UPOWER_MEMBER_RANK = TypeAdapter(MemberRankData)
_REMARK_LIST = TypeAdapter(ElecRemarkList)
_REMARK_DETAIL = TypeAdapter(ElecRemarkDetail)
_BCOIN_QUICK_PAY = TypeAdapter(BcoinQuickPayData)
_OPTIONAL_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_INT = TypeAdapter(int)


class ElectricClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def month_up_list(self, *, up_mid: int) -> ChargeMonthUpData:
        return await self._client._get_payload(
            "/x/ugcpay-rank/elec/month/up", month_up_list_query(up_mid), _MONTH_UP_LIST
        )

    async def video_show(
        self, *, mid: int, aid: int | None = None, bvid: str | None = None
    ) -> VideoElecShowData:
        return await self._client._get_payload(
            "/x/web-interface/elec/show", video_show_query(mid, aid, bvid), _VIDEO_SHOW
        )

    async def recharge_list(
        self,
        *,
        page: int,
        page_size: int,
        begin_time: date | None = None,
        end_time: date | None = None,
    ) -> RechargeData:
        return await self._client._get_payload(
            "/bk/brokerage/listForCustomerRechargeRecord",
            recharge_list_query(page, page_size, begin_time, end_time),
            _RECHARGE_LIST,
            host="pay.bilibili.com",
        )

    async def rank_recent(self, *, pn: int | None = None, ps: int | None = None) -> ElecRankData:
        return await self._client._get_payload(
            "/x/h5/elec/rank/recent",
            rank_recent_query(pn, ps),
            _RANK_RECENT,
            host="member.bilibili.com",
        )

    async def charge_record(self, *, page: int, charge_type: int) -> ChargeRecordData:
        return await self._client._get_payload(
            "/xlive/revenue/v1/guard/getChargeRecord",
            charge_record_query(page, charge_type),
            _CHARGE_RECORD,
            host="api.live.bilibili.com",
        )

    async def upower_item_detail(self, *, up_mid: int) -> UpowerItemDetail:
        return await self._client._get_payload(
            "/x/upower/item/detail", month_up_list_query(up_mid), _UPOWER_ITEM_DETAIL
        )

    async def charge_follow_info(self, *, up_mid: int) -> ChargeFollowInfo:
        return await self._client._get_payload(
            "/x/upower/charge/follow/info", month_up_list_query(up_mid), _CHARGE_FOLLOW_INFO
        )

    async def upower_member_rank(
        self,
        *,
        up_mid: int,
        pn: int,
        ps: int,
        privilege_type: int | None = None,
    ) -> MemberRankData:
        return await self._client._get_payload(
            "/x/upower/up/member/rank/v2",
            upower_member_rank_query(up_mid, pn, ps, privilege_type),
            _UPOWER_MEMBER_RANK,
        )

    async def remark_list(
        self,
        *,
        pn: int | None = None,
        ps: int | None = None,
        begin: date | None = None,
        end: date | None = None,
    ) -> ElecRemarkList:
        return await self._client._get_payload(
            "/x/web/elec/remark/list",
            remark_list_query(pn, ps, begin, end),
            _REMARK_LIST,
            host="member.bilibili.com",
        )

    async def remark_detail(self, *, id: int) -> ElecRemarkDetail:
        return await self._client._get_payload(
            "/x/web/elec/remark/detail",
            remark_detail_query(id),
            _REMARK_DETAIL,
            host="member.bilibili.com",
        )

    async def bcoin_quick_pay(
        self,
        *,
        bp_num: int,
        is_bp_remains_prior: bool,
        up_mid: int,
        otype: str,
        oid: int,
    ) -> BcoinQuickPayData:
        form = bcoin_quick_pay_form(
            bp_num, is_bp_remains_prior, up_mid, otype, oid, csrf=""
        )
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/ugcpay/web/v2/trade/elec/pay/quick", {}, _BCOIN_QUICK_PAY, form=form
        )

    async def send_message(self, *, order_id: str, message: str) -> JsonValue:
        form = message_form(order_id, message, csrf="")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/ugcpay/trade/elec/message", {}, _OPTIONAL_JSON, form=form, optional=True
        )

    async def reply_remark(self, *, id: int, msg: str) -> int:
        form = reply_remark_form(id, msg, csrf="")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/web/elec/remark/reply",
            {},
            _INT,
            form=form,
            host="member.bilibili.com",
        )
