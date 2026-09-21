from __future__ import annotations

from bpi._core.response import ResponseModel


class IpInfo(ResponseModel):
    country: str | None = None
    province: str | None = None
    city: str | None = None
    isp: str | None = None
    addr: str | None = None
