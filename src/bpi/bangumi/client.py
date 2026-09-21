from __future__ import annotations

from pydantic import TypeAdapter

from bpi._core.params import integer
from bpi._generated.bangumi_client import BangumiReadMethods
from bpi._generated.bangumi_models import BangumiDetailResult
from bpi.errors import InvalidParameterError

from .actions import BangumiActionMethods
from .models import BangumiVideoStreamData

_STREAM = TypeAdapter(BangumiVideoStreamData)


class BangumiClient(BangumiReadMethods, BangumiActionMethods):
    """Bangumi API entry point; generated read methods are inherited."""

    async def detail(
        self, *, season_id: int | None = None, ep_id: int | None = None
    ) -> BangumiDetailResult:
        if (season_id is None) == (ep_id is None):
            raise InvalidParameterError("Provide exactly one of season_id or ep_id")
        if season_id is not None:
            return await self.detail_by_season_id(season_id=season_id)
        if ep_id is None:
            raise InvalidParameterError("Provide exactly one of season_id or ep_id")
        return await self.detail_by_ep_id(episode_id=ep_id)

    async def video_stream(
        self,
        *,
        ep_id: int | None = None,
        cid: int | None = None,
        quality: int | None = None,
        format_flags: int | None = None,
    ) -> BangumiVideoStreamData:
        if (ep_id is None) == (cid is None):
            raise InvalidParameterError("Provide exactly one of ep_id or cid")
        params: dict[str, str] = {"fnver": "0"}
        if ep_id is not None:
            params["ep_id"] = integer(ep_id, "ep_id")
        else:
            if cid is None:
                raise InvalidParameterError("Provide exactly one of ep_id or cid")
            params["cid"] = integer(cid, "cid")
        if quality is not None:
            params["qn"] = integer(quality, "quality", 0)
        if format_flags is not None:
            flags = int(integer(format_flags, "format_flags", 0))
            params["fnval"] = str(flags)
            if flags & (128 | 1024):
                params["fourk"] = "1"
        return await self._client._get_payload("/pgc/player/web/playurl", params, _STREAM)
