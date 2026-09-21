from __future__ import annotations

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel


class Season(ResponseModel):
    id: int
    title: str
    desc: str
    cover: str
    is_end: int = Field(alias="isEnd")
    mid: int
    is_act: int = Field(alias="isAct")
    is_pay: int
    state: int
    part_state: int = Field(alias="partState")
    sign_state: int = Field(alias="signState")
    reject_reason: str | None = Field(alias="rejectReason")
    ctime: int
    mtime: int
    no_section: int
    forbid: int
    protocol_id: str | None
    ep_num: int
    season_price: int
    is_opened: int
    has_charging_pay: int
    has_pugv_pay: int | None = None
    season_upfrom: int | None = Field(default=None, alias="SeasonUpfrom")


class Section(ResponseModel):
    id: int
    section_type: int = Field(alias="type")
    season_id: int = Field(alias="seasonId")
    title: str
    order: int
    state: int
    part_state: int = Field(alias="partState")
    ctime: int
    mtime: int
    ep_count: int = Field(alias="epCount")
    cover: str
    has_charging_pay: int
    show: int | None = None
    has_pugv_pay: int | None = None
    reject_reason: str | None = Field(default=None, alias="rejectReason")
    episodes: JsonValue | None = Field(default=None, alias="Episodes")


class CheckInInfo(ResponseModel):
    status: int
    status_reason: str | None
    season_status: int


class SeasonStat(ResponseModel):
    view: int
    danmaku: int
    reply: int
    fav: int
    coin: int
    share: int
    now_rank: int = Field(alias="nowRank")
    his_rank: int = Field(alias="hisRank")
    like: int
    subscription: int
    vt: int


class SectionsWrapper(ResponseModel):
    sections: list[Section]


class PartEpisode(ResponseModel):
    id: int
    title: str
    aid: int
    bvid: str
    cid: int
    season_id: int = Field(alias="seasonId")
    section_id: int = Field(alias="sectionId")
    order: int
    video_title: str | None = Field(alias="videoTitle")
    archive_title: str | None = Field(alias="archiveTitle")
    archive_state: int = Field(alias="archiveState")
    reject_reason: str | None = Field(alias="rejectReason")
    state: int
    cover: str
    is_free: int
    aid_owner: bool
    charging_pay: int


class SeasonItem(ResponseModel):
    season: Season
    course: JsonValue | None
    checkin: CheckInInfo | None
    season_stat: SeasonStat | None = Field(alias="seasonStat")
    sections: SectionsWrapper | None
    part_episodes: list[PartEpisode]


class SeasonListData(ResponseModel):
    seasons: list[SeasonItem]
    tip: JsonValue
    total: int
    play_type: int


class SeasonInfoSections(ResponseModel):
    sections: list[Section]
    total: int


class SeasonInfoData(ResponseModel):
    season: Season
    course: JsonValue
    checkin: JsonValue
    season_stat: JsonValue = Field(alias="seasonStat")
    sections: SeasonInfoSections
    part_episodes: JsonValue


class SeasonByAidData(ResponseModel):
    id: int
    title: str
    desc: str | None
    cover: str
    is_end: int = Field(alias="isEnd")
    mid: int
    is_act: int = Field(alias="isAct")
    is_pay: int
    state: int
    part_state: int = Field(alias="partState")
    sign_state: int = Field(alias="signState")
    reject_reason: str | None = Field(alias="rejectReason")
    ctime: int
    mtime: int
    no_section: int
    forbid: int
    protocol_id: str | None
    ep_num: int
    season_price: int
    is_opened: int
    has_charging_pay: int
    has_pugv_pay: int


class SeasonSectionInfo(ResponseModel):
    id: int
    section_type: int = Field(alias="type")
    season_id: int = Field(alias="seasonId")
    title: str
    order: int
    state: int
    part_state: int = Field(alias="partState")
    reject_reason: str = Field(alias="rejectReason")
    ctime: int
    mtime: int
    ep_count: int = Field(alias="epCount")
    cover: str
    has_charging_pay: int
    episodes: JsonValue = Field(alias="Episodes")
    show: int
    has_pugv_pay: int


class SeasonSectionEpisode(ResponseModel):
    id: int
    title: str
    aid: int
    bvid: str
    cid: int
    season_id: int = Field(alias="seasonId")
    section_id: int = Field(alias="sectionId")
    order: int
    video_title: str | None = Field(alias="videoTitle")
    archive_title: str | None = Field(alias="archiveTitle")
    archive_state: int = Field(alias="archiveState")
    reject_reason: str | None = Field(alias="rejectReason")
    state: int
    cover: str
    is_free: int
    aid_owner: bool
    charging_pay: int


class SeasonSectionEpisodesData(ResponseModel):
    section: SeasonSectionInfo
    episodes: list[SeasonSectionEpisode] | None


class ArchiveStat(ResponseModel):
    aid: int
    view: int
    danmaku: int
    reply: int
    favorite: int
    coin: int
    share: int
    now_rank: int
    his_rank: int
    like: int
    dislike: int
    vt: int
    vv: int


class Archive(ResponseModel):
    aid: int
    bvid: str
    title: str
    cover: str
    duration: int
    desc: str


class ArcAudit(ResponseModel):
    archive: Archive | None = Field(alias="Archive")
    videos: JsonValue | None = Field(alias="Videos")
    stat: ArchiveStat
    state_panel: int
    parent_tname: str | None
    typename: str | None
    open_appeal: int
    activity: JsonValue | None
    season_add_state: int


class PageInfo(ResponseModel):
    pn: int
    ps: int
    count: int


class SpArchivesData(ResponseModel):
    arc_audits: list[ArcAudit]
    page: PageInfo
    play_type: int


class VideoPart(ResponseModel):
    cid: int
    index: int
    title: str
    duration: int


class ArchiveInfo(ResponseModel):
    aid: int
    bvid: str
    title: str


class ArchiveVideosData(ResponseModel):
    archive: ArchiveInfo
    videos: list[VideoPart]


class UpStatData(ResponseModel):
    inc_coin: int
    inc_elec: int
    inc_fav: int
    inc_like: int
    inc_share: int
    incr_click: int
    incr_dm: int
    incr_fans: int
    incr_reply: int
    total_click: int
    total_coin: int
    total_dm: int
    total_elec: int
    total_fans: int
    total_fav: int
    total_like: int
    total_reply: int
    total_share: int


class ArchiveCompareStat(ResponseModel):
    not_ready_field: JsonValue
    play: int
    vt: int
    full_play_ratio: int
    play_viewer_rate: int
    play_viewer_rate_med: int
    play_fan_rate: int
    play_fan_rate_med: int
    active_fans_rate: int
    active_fans_med: int
    tm_rate: int
    tm_rate_med: int
    tm_fan_simi_rate_med: int
    tm_viewer_simi_rate_med: int
    tm_fan_rate: int
    tm_viewer_rate: int
    tm_pass_rate: int
    tm_fan_pass_rate: int
    tm_viewer_pass_rate: int
    crash_rate: int
    crash_rate_med: int
    crash_fan_simi_rate_med: int
    crash_viewer_simi_rate_med: int
    crash_fan_rate: int
    crash_viewer_rate: int
    interact_rate: int
    interact_rate_med: int
    interact_fan_simi_rate_med: int
    interact_viewer_simi_rate_med: int
    interact_fan_rate: int
    interact_viewer_rate: int
    avg_play_time: int
    avg_play_time_int: int
    total_new_attention_cnt: int
    play_trans_fan_rate: int
    play_trans_fan_rate_med: int
    like: int
    comment: int
    dm: int
    fav: int
    coin: int
    share: int
    unfollow: int
    tm_star: int
    tm_viewer_star: int
    tm_fan_star: int
    crash_p50: int
    crash_viewer_p50: int
    crash_fan_p50: int
    interact_p50: int
    interact_viewer_p50: int
    interact_fan_p50: int
    play_trans_fan_p50: int


class ArchiveCompareHourStat(ResponseModel):
    not_ready_field: JsonValue
    play: int
    vt: int
    like: int
    comment: int
    dm: int
    fav: int
    coin: int
    share: int
    tm_pass_rate: int
    interact_rate: int
    tm_star: int


class ArchiveCompareItem(ResponseModel):
    aid: int
    bvid: str
    cover: str
    title: str
    pubtime: int
    duration: int
    stat: ArchiveCompareStat
    is_only_self: bool
    hour_stat: ArchiveCompareHourStat | None


class ArchiveCompareData(ResponseModel):
    list: list[ArchiveCompareItem]


class UpArticleStatData(ResponseModel):
    view: int
    reply: int
    like: int
    coin: int
    fav: int
    share: int
    incr_view: int
    incr_reply: int
    incr_like: int
    incr_coin: int
    incr_fav: int
    incr_share: int


class VideoTrendItem(ResponseModel):
    date_key: int
    total_inc: int


class ArticleTrendItem(ResponseModel):
    date_key: int
    total_inc: int


class PageSource(ResponseModel):
    dynamic: int
    other: int
    related_video: int
    search: int
    space: int
    tenma: int


class PlayProportion(ResponseModel):
    android: int
    h5: int
    ios: int
    out: int
    pc: int


class PlaySourceData(ResponseModel):
    page_source: PageSource
    play_proportion: PlayProportion


class Period(ResponseModel):
    module_one: str | None
    module_two: str | None
    module_three: str | None
    module_four: str | None


class ViewerArea(ResponseModel):
    fan: dict[str, int]
    not_fan: dict[str, int]


class ViewerBaseDetail(ResponseModel):
    male: int
    female: int
    age_one: int
    age_two: int
    age_three: int
    age_four: int
    plat_pc: int
    plat_h5: int
    plat_out: int
    plat_ios: int
    plat_android: int
    plat_other_app: int


class ViewerBase(ResponseModel):
    fan: ViewerBaseDetail
    not_fan: ViewerBaseDetail


class ViewerData(ResponseModel):
    period: Period
    viewer_area: ViewerArea
    viewer_base: ViewerBase


class ElectromagneticInfo(ResponseModel):
    mid: int
    level: int
    score: int
    credit: int
    state: int
    update_date: int


class UploadCoverData(ResponseModel):
    url: str


class EpisodeAdd(ResponseModel):
    title: str
    aid: int = Field(gt=0)
    cid: int = Field(gt=0)
    charging_pay: int = Field(default=0, ge=0)
    member_first: int = Field(default=0, ge=0)
    limited_free: bool = False


class SeasonEdit(ResponseModel):
    id: int = Field(gt=0)
    title: str
    cover: str
    desc: str | None = None
    season_price: int | None = Field(default=None, ge=0)
    is_end: int | None = Field(default=None, alias="isEnd", ge=0, le=1)


class SeasonSectionEdit(ResponseModel):
    id: int = Field(gt=0)
    type_field: int = Field(alias="type", ge=0)
    season_id: int = Field(alias="seasonId", gt=0)
    title: str


class SectionSort(ResponseModel):
    id: int = Field(gt=0)
    order: int = Field(ge=0)


class EpisodeSort(ResponseModel):
    id: int = Field(gt=0)
    sort: int = Field(ge=0)


class EpisodeEdit(ResponseModel):
    id: int = Field(gt=0)
    title: str
    aid: int = Field(gt=0)
    cid: int = Field(gt=0)
    season_id: int = Field(alias="seasonId", gt=0)
    section_id: int = Field(alias="sectionId", gt=0)
    sorts: list[EpisodeSort] = Field(default_factory=list)
    order: int = Field(ge=0)


class SeasonSectionSort(ResponseModel):
    id: int = Field(gt=0)
    sort: int = Field(ge=0)


class Episode(ResponseModel):
    title: str
    aid: int = Field(gt=0)
    cid: int = Field(gt=0)
    charging_pay: int = Field(ge=0)
    member_first: int = Field(ge=0)
    limited_free: bool
