from __future__ import annotations

from pydantic import AliasChoices, Field, JsonValue, field_validator

from bpi._core.response import ResponseModel


class FavFolderUpper(ResponseModel):
    mid: int
    name: str
    face: str
    followed: bool
    vip_type: int
    vip_status: int = Field(alias="vip_statue")


class FavFolderCntInfo(ResponseModel):
    collect: int
    play: int
    thumb_up: int
    share: int


class FavFolderInfo(ResponseModel):
    id: int
    fid: int
    mid: int
    attr: int
    title: str
    cover: str
    upper: FavFolderUpper
    cover_type: int
    cnt_info: FavFolderCntInfo
    type_name: int = Field(alias="type")
    intro: str
    ctime: int
    mtime: int
    state: int
    fav_state: int
    like_state: int
    media_count: int


class CreatedFolderItem(ResponseModel):
    id: int
    fid: int
    mid: int
    attr: int
    title: str
    fav_state: int
    media_count: int


class CreatedFolderListData(ResponseModel):
    count: int
    list: list[CreatedFolderItem]


class CollectedFolderUpper(ResponseModel):
    mid: int
    name: str
    face: str


class CollectedFolderItem(ResponseModel):
    id: int
    fid: int
    mid: int
    attr: int
    title: str
    cover: str
    upper: CollectedFolderUpper
    cover_type: int
    intro: str
    ctime: int
    mtime: int
    state: int
    fav_state: int
    media_count: int


class CollectedFolderListData(ResponseModel):
    count: int
    list: list[CollectedFolderItem]


class ResourceInfoUpper(ResponseModel):
    mid: int
    name: str
    face: str


class ResourceInfoCntInfo(ResponseModel):
    collect: int
    play: int
    danmaku: int


class ResourceInfoItem(ResponseModel):
    id: int
    type_name: int = Field(alias="type")
    title: str
    cover: str
    intro: str
    page: int | None = None
    duration: int
    upper: ResourceInfoUpper
    attr: int
    cnt_info: ResourceInfoCntInfo
    link: str
    ctime: int
    pubtime: int
    fav_time: int
    bv_id: str | None = None
    bvid: str | None = None
    season: JsonValue | None = None


class FavListUpper(ResponseModel):
    mid: int
    name: str
    face: str
    followed: bool | None = None
    vip_type: int | None = None
    vip_status: int | None = Field(
        default=None,
        validation_alias=AliasChoices("vip_status", "vip_statue"),
    )


class FavListCntInfo(ResponseModel):
    collect: int
    play: int
    share: int | None = None
    thumb_up: int | None = None
    danmaku: int | None = None
    view_text_1: str | None = None


class FavListInfo(ResponseModel):
    id: int
    fid: int
    mid: int
    attr: int
    title: str
    cover: str
    upper: FavListUpper
    cover_type: int
    cnt_info: FavListCntInfo
    type_name: int = Field(alias="type")
    intro: str
    ctime: int
    mtime: int
    state: int
    fav_state: int
    like_state: int
    media_count: int


class FavListMedia(ResponseModel):
    id: int
    type_name: int = Field(alias="type")
    title: str
    cover: str
    intro: str
    page: int | None = None
    duration: int
    upper: FavListUpper
    attr: int
    cnt_info: FavListCntInfo
    link: str
    ctime: int
    pubtime: int
    fav_time: int
    bv_id: str | None = None
    bvid: str | None = None
    season: JsonValue | None = None


class FavListDetailData(ResponseModel):
    info: FavListInfo
    medias: list[FavListMedia] = Field(default_factory=list)
    has_more: bool
    ttl: int

    @field_validator("medias", mode="before")
    @classmethod
    def null_medias_are_empty(cls, value: object) -> object:
        return [] if value is None else value


class FavResourceIdItem(ResponseModel):
    id: int
    type_name: int = Field(alias="type")
    bv_id: str | None = None
    bvid: str | None = None
