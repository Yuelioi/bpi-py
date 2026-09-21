from __future__ import annotations

from bpi._core.response import ResponseModel


class SpaceCover(ResponseModel):
    height: int
    url: str
    width: int


class SpaceStat(ResponseModel):
    like: str
    view: str | None = None


class SpaceItem(ResponseModel):
    content: str
    cover: SpaceCover | None = None
    jump_url: str
    opus_id: str
    stat: SpaceStat


class SpaceData(ResponseModel):
    has_more: bool
    items: list[SpaceItem]
    offset: str
    update_num: int
