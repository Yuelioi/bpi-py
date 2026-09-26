from __future__ import annotations

from pydantic import Field, JsonValue, field_validator

from bpi._core.response import ResponseModel
from bpi.video.models import DashFlac, DashStream, DurlInfo, SupportFormat


class CourseDashDolby(ResponseModel):
    type: int
    audio: list[DashStream]

    @field_validator("type", mode="before")
    @classmethod
    def default_invalid_type(cls, value: object) -> object:
        # Rust uses serde_with::DefaultOnError here; e.g. cheese can return "NONE".
        return value if type(value) is int else 0


class CourseDashInfo(ResponseModel):
    duration: int
    min_buffer_time: float | None = None
    video: list[DashStream]
    audio: list[DashStream]
    dolby: CourseDashDolby | None = None
    flac: DashFlac | None = None


class MultiSceneArgs(ResponseModel):
    normal_target_i: str
    undersized_target_i: str
    high_dynamic_target_i: str


class CourseVolume(ResponseModel):
    measured_i: float
    target_i: float
    target_offset: float
    measured_lra: float
    target_tp: float
    measured_tp: float
    measured_threshold: float
    multi_scene_args: MultiSceneArgs


class FileInfoEntry(ResponseModel):
    ahead: str
    vhead: str
    filesize: int
    order: int
    timelength: int


class FileInfo(ResponseModel):
    infos: list[FileInfoEntry]


class CourseVideoInfo(ResponseModel):
    no_rexcode: int
    fnval: int
    video_project: bool
    expire_time: int
    backup_url: list[JsonValue | None]
    fnver: int
    support_formats: list[str]
    support_description: list[str]
    video_info_type: str = Field(alias="type")
    url: str
    quality: int
    timelength: int
    volume: CourseVolume
    accept_formats: list[SupportFormat]
    support_quality: list[int]
    file_info: dict[str, FileInfo]
    dash: CourseDashInfo
    video_codecid: int
    cid: int


class FragmentInfo(ResponseModel):
    fragment_type: str
    index: int
    aid: int
    fragment_position: str
    cid: int


class FragmentVideo(ResponseModel):
    fragment_info: FragmentInfo
    playable_status: bool
    video_info: CourseVideoInfo


class CourseHlsTrack(ResponseModel):
    id: int
    stream_url: str


class CourseHlsStreams(ResponseModel):
    video: list[CourseHlsTrack] = Field(default_factory=list)
    audio: list[CourseHlsTrack] = Field(default_factory=list)


class CourseVideoStreamData(ResponseModel):
    """Course playurl payload with the Rust flattened common stream fields."""

    quality: int
    accept_quality: list[int] = Field(default_factory=list)
    accept_format: str = ""
    accept_description: list[str] = Field(default_factory=list)
    format: str
    video_codecid: int
    durl: list[DurlInfo] | None = None
    dash: CourseDashInfo | None = None
    has_paid: bool
    support_formats: list[SupportFormat]
    timelength: int | None = None
    fnval: int | None = None
    is_preview: int | None = None
    is_drm: bool | None = None
    drm_type: str | None = None
    drm_tech_type: int | None = None
    hls: CourseHlsStreams | None = None

    seek_param: str
    video_project: bool
    data_type: str = Field(alias="type")
    result: str
    seek_type: str
    from_: str = Field(alias="from")
    no_rexcode: int
    message: str
    fragment_videos: list[FragmentVideo] | None = None
    status: int
