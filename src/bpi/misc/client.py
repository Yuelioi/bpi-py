from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from .models import Buvid3Data, BuvidData, ShortLinkData, TicketData
from .params import b23_short_link_form
from .sign import ticket_request_params

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_BUVID3 = TypeAdapter(Buvid3Data)
_BUVID = TypeAdapter(BuvidData)
_SHORT_LINK = TypeAdapter(ShortLinkData)
_TICKET = TypeAdapter(TicketData)


class MiscClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def buvid3(self) -> Buvid3Data:
        return await self._client._get_payload(
            "/x/web-frontend/getbuvid",
            {},
            _BUVID3,
        )

    async def buvid(self) -> BuvidData:
        return await self._client._get_payload(
            "/x/frontend/finger/spi",
            {},
            _BUVID,
        )

    async def b23_short_link(
        self,
        aid: int,
        *,
        platform: str = "unix",
        share_channel: str = "COPY",
        share_id: str = "main.ugc-video-detail.0.0.pv",
        share_mode: int = 4,
        buvid: str = "qwq",
        build: int = 6_114_514,
    ) -> ShortLinkData:
        data = await self._client._post_payload(
            "/x/share/click",
            {},
            _SHORT_LINK,
            form=b23_short_link_form(
                aid,
                platform=platform,
                share_channel=share_channel,
                share_id=share_id,
                share_mode=share_mode,
                buvid=buvid,
                build=build,
            ),
            host="api.biliapi.net",
        )
        data.extract()
        return data

    async def bili_ticket(self) -> TicketData:
        timestamp = int(self._client._clock())
        csrf = self._client._csrf(optional=True)
        return await self._client._post_payload(
            "/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket",
            ticket_request_params(timestamp, csrf),
            _TICKET,
        )

    async def bili_ticket_string(self) -> str:
        return (await self.bili_ticket()).ticket
