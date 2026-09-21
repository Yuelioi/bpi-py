from __future__ import annotations

from bpi._core.response import ResponseModel


class ActivityInfoData(ResponseModel):
    id: int
    stime: int
    etime: int
    ctime: int
    mtime: int
    name: str
    act_url: str
    cover: str
    dic: str
    h5_cover: str
    android_url: str
    ios_url: str
    child_sids: str
    lid: int | None = None


class ActivityItem(ResponseModel):
    id: int
    state: int
    stime: int
    etime: int
    ctime: int
    mtime: int
    name: str
    h5_url: str
    h5_cover: str
    page_name: str
    plat: int
    desc: str


class ActivityListData(ResponseModel):
    list: list[ActivityItem]
    num: int
    size: int
    total: int
