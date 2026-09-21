from __future__ import annotations

from bpi._core.response import ResponseModel
from bpi.video.models import DashInfo, DurlInfo, SupportFormat


class VipLabel(ResponseModel):
    """Shared VIP label used by bangumi UP metadata."""

    text: str = ""
    label_theme: str = ""
    text_color: str = ""
    bg_style: int = 0
    bg_color: str = ""


class BangumiRecordInfo(ResponseModel):
    record_icon: str
    record: str


class BangumiVideoStreamData(ResponseModel):
    """Bangumi playurl payload with the Rust flattened common stream fields."""

    quality: int
    accept_quality: list[int]
    accept_format: str
    accept_description: list[str]
    format: str
    video_codecid: int
    durl: list[DurlInfo] | None = None
    dash: DashInfo | None = None
    has_paid: bool
    support_formats: list[SupportFormat]
    timelength: int | None = None
    fnval: int | None = None
    is_preview: int | None = None

    code: int
    fnver: int
    video_project: bool
    type: str
    bp: int
    vip_type: int | None = None
    vip_status: int | None = None
    is_drm: bool
    no_rexcode: int
    record_info: BangumiRecordInfo | None = None


class BangumiFollowResult(ResponseModel):
    fmid: int
    relation: bool
    status: int
    toast: str
