from __future__ import annotations

from pydantic import AliasChoices, Field, JsonValue, field_validator

from bpi._core.response import ResponseModel


class VideoOwner(ResponseModel):
    mid: int
    name: str
    face: str


class VideoStat(ResponseModel):
    aid: int
    view: int
    danmaku: int
    reply: int
    favorite: int | None = None
    fav: int | None = None
    coin: int
    share: int
    like: int


class VideoPage(ResponseModel):
    cid: int
    page: int
    part: str
    duration: int


class VideoView(ResponseModel):
    aid: int
    bvid: str
    videos: int
    title: str
    pic: str
    owner: VideoOwner
    stat: VideoStat
    cid: int
    pages: list[VideoPage] = Field(default_factory=list)


class DashStream(ResponseModel):
    id: int
    base_url: str = Field(validation_alias=AliasChoices("baseUrl", "base_url"))
    backup_url: list[str] = Field(
        default_factory=list, validation_alias=AliasChoices("backupUrl", "backup_url")
    )
    bandwidth: int
    mime_type: str = Field(validation_alias=AliasChoices("mimeType", "mime_type"))
    codecs: str
    width: int | None = None
    height: int | None = None
    frame_rate: str | None = Field(
        default=None, validation_alias=AliasChoices("frameRate", "frame_rate")
    )
    sar: str | None = None
    start_with_sap: int | None = None
    segment_base: JsonValue = None
    md5: str | None = None
    size: int | None = None
    db_type: int | None = None
    type: str | None = None
    stream_name: str | None = None
    orientation: int | None = None

    @field_validator("backup_url", mode="before")
    @classmethod
    def empty_backup(cls, value: object) -> object:
        return [] if value is None else value


class DashDolby(ResponseModel):
    type: int
    audio: list[DashStream] | None = None


class DashFlac(ResponseModel):
    display: bool | None = None
    audio: DashStream | None = None


class DashInfo(ResponseModel):
    video: list[DashStream]
    audio: list[DashStream]
    dolby: DashDolby | None = None
    flac: DashFlac | None = None
    duration: int


class DurlInfo(ResponseModel):
    order: int
    length: int
    size: int
    ahead: str
    vhead: str
    url: str
    backup_url: list[str] = Field(default_factory=list)

    @field_validator("backup_url", mode="before")
    @classmethod
    def empty_backup(cls, value: object) -> object:
        return [] if value is None else value


class SupportFormat(ResponseModel):
    quality: int
    format: str
    new_description: str
    display_desc: str
    superscript: str
    codecs: list[str] | None = None


class PlayUrlResponseData(ResponseModel):
    from_: str = Field(alias="from")
    result: str
    message: str
    quality: int
    format: str
    timelength: int
    accept_format: str
    accept_description: list[str]
    accept_quality: list[int]
    video_codecid: int
    seek_param: str
    seek_type: str
    durl: list[DurlInfo] | None = None
    dash: DashInfo | None = None
    support_formats: list[SupportFormat]
    high_format: JsonValue = None
    last_play_time: int
    last_play_cid: int
