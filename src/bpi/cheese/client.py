from __future__ import annotations

from pydantic import TypeAdapter

from bpi._core.params import integer
from bpi._generated.cheese_client import CheeseReadMethods
from bpi._generated.cheese_models import CourseInfo
from bpi.errors import InvalidParameterError

from .models import CourseVideoStreamData

_STREAM = TypeAdapter(CourseVideoStreamData)


class CheeseClient(CheeseReadMethods):
    """PUGV/course API entry point."""

    async def info(
        self, *, season_id: int | None = None, ep_id: int | None = None
    ) -> CourseInfo:
        if (season_id is None) == (ep_id is None):
            raise InvalidParameterError("Provide exactly one of season_id or ep_id")
        if season_id is not None:
            return await self.info_by_season_id(season_id=season_id)
        if ep_id is None:
            raise InvalidParameterError("Provide exactly one of season_id or ep_id")
        return await self.info_by_ep_id(episode_id=ep_id)

    async def video_stream(
        self,
        *,
        aid: int,
        ep_id: int,
        cid: int,
        quality: int | None = None,
        format_flags: int | None = None,
    ) -> CourseVideoStreamData:
        params = {
            "avid": integer(aid, "aid"),
            "ep_id": integer(ep_id, "ep_id"),
            "cid": integer(cid, "cid"),
            "fnver": "0",
        }
        if quality is not None:
            params["qn"] = integer(quality, "quality")
        if format_flags is not None:
            flags = int(integer(format_flags, "format_flags"))
            params["fnval"] = str(flags)
            if flags & (128 | 1024):
                params["fourk"] = "1"
        return await self._client._get_payload("/pugv/player/web/playurl", params, _STREAM)
