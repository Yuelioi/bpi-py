from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from bpi._core.params import integer, video_id
from bpi._generated.video_client import VideoReadMethods
from bpi.errors import InvalidParameterError
from bpi.video.actions import VideoActionMethods
from bpi.video.models import PlayUrlResponseData, VideoPage, VideoView

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient

VIEW = TypeAdapter(VideoView)
PAGES = TypeAdapter(list[VideoPage])
PLAY = TypeAdapter(PlayUrlResponseData)


class VideoClient(VideoReadMethods, VideoActionMethods):
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def view(self, *, aid: int | None = None, bvid: str | None = None) -> VideoView:
        """Get video metadata by exactly one AV or BV identifier."""
        return await self._client._get_payload("/x/web-interface/view", video_id(aid, bvid), VIEW)

    async def page_list(
        self, *, aid: int | None = None, bvid: str | None = None
    ) -> list[VideoPage]:
        """Get video parts and their content IDs."""
        return await self._client._get_payload("/x/player/pagelist", video_id(aid, bvid), PAGES)

    async def play_url(
        self,
        *,
        cid: int,
        aid: int | None = None,
        bvid: str | None = None,
        quality: int | None = None,
        format_flags: int | None = None,
        format_version: int | None = None,
        fourk: bool | None = None,
        platform: str = "pc",
        high_quality: bool | None = None,
        try_look: bool | None = None,
    ) -> PlayUrlResponseData:
        """Get WBI-signed playback URLs; quality availability depends on the account."""
        params = video_id(aid, bvid, play=True)
        params["cid"] = integer(cid, "cid")
        if not isinstance(platform, str) or not platform.strip():
            raise InvalidParameterError("platform must be nonempty")
        params["platform"] = platform
        for key, value in (("qn", quality), ("fnval", format_flags), ("fnver", format_version)):
            if value is not None:
                params[key] = integer(value, key, 0)
        for key, flag in (("fourk", fourk), ("high_quality", high_quality), ("try_look", try_look)):
            if flag is not None:
                if type(flag) is not bool:
                    raise InvalidParameterError(f"{key} must be a boolean")
                params[key] = "1" if flag else "0"
        signed = await self._client._sign(params)
        return await self._client._get_payload("/x/player/wbi/playurl", signed, PLAY)
