from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from .models import VipCenterData, VipExperienceData
from .params import center_info_query, privilege_type

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_CENTER = TypeAdapter(VipCenterData)
_EXPERIENCE = TypeAdapter(VipExperienceData)
_OPTIONAL_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class VipClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def center_info(self, *, build: int = 0) -> VipCenterData:
        return await self._client._get_payload(
            "/x/vip/web/vip_center/combine",
            center_info_query(build),
            _CENTER,
        )

    async def receive_privilege(self, *, privilege_type_id: int) -> JsonValue:
        form = {
            "type": privilege_type(privilege_type_id),
            "csrf": self._client.csrf(),
        }
        return await self._client._post_payload(
            "/x/vip/privilege/receive",
            {},
            _OPTIONAL_JSON,
            form=form,
            optional=True,
        )

    async def add_experience(self) -> VipExperienceData:
        form = {"csrf": self._client.csrf()}
        return await self._client._post_payload(
            "/x/vip/experience/add",
            {},
            _EXPERIENCE,
            form=form,
        )
