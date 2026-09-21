from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from bpi.errors import InvalidParameterError

from .models import IpInfo

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_IP_INFO = TypeAdapter(IpInfo)


class ClientInfoClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def ip(
        self,
        *,
        ip: str | IPv4Address | IPv6Address | None = None,
    ) -> IpInfo:
        params: dict[str, str] = {}
        if ip is not None:
            if not isinstance(ip, (str, IPv4Address, IPv6Address)):
                raise InvalidParameterError("ip must be a valid IPv4 or IPv6 address")
            try:
                parsed = ip_address(ip.strip() if isinstance(ip, str) else ip)
            except ValueError:
                raise InvalidParameterError("ip must be a valid IPv4 or IPv6 address") from None
            params["ip"] = str(parsed)

        return await self._client._get_payload(
            "/ip_service/v1/ip_service/get_ip_addr",
            params,
            _IP_INFO,
            host="api.live.bilibili.com",
        )
