from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from bpi.errors import InvalidParameterError

from .models import UserWallet

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_WALLET = TypeAdapter(UserWallet)


class WalletClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def info(
        self,
        *,
        timestamp_ms: int | None = None,
        platform_type: int = 3,
        trace_id: int | None = None,
        version: str = "1.0",
    ) -> UserWallet:
        if type(platform_type) is not int or platform_type <= 0:
            raise InvalidParameterError("platform_type must be positive")
        if timestamp_ms is None:
            timestamp_ms = int(self._client._clock() * 1000)
        elif type(timestamp_ms) is not int:
            raise InvalidParameterError("timestamp_ms must be an integer")
        if trace_id is None:
            trace_id = timestamp_ms
        elif type(trace_id) is not int or trace_id <= 0:
            raise InvalidParameterError("trace_id must be positive")
        if not isinstance(version, str) or not version.strip():
            raise InvalidParameterError("version cannot be blank")

        body: dict[str, object] = {
            "csrf": self._client.csrf(),
            "platformType": platform_type,
            "timestamp": timestamp_ms,
            "traceId": trace_id,
            "version": version.strip(),
        }
        return await self._client._post_json_payload(
            "/paywallet/wallet/getUserWallet",
            {},
            _WALLET,
            json_body=body,
            host="pay.bilibili.com",
        )
