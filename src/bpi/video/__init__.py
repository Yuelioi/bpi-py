from bpi._generated.video_models import (
    AiSummaryResponseData,
    GetSeasonsArchivesData,
    GetSeasonsSeriesData,
    GetSeriesArchivesData,
    GetSeriesData,
    InteractiveVideoInfoResponseData,
    OnlineTotalResponseData,
    PlayerInfoResponseData,
    RcmdFeedResponseData,
    RelatedVideo,
    VideoDetail,
    VideoDetailTag,
    VideoTag,
)

from .actions import CoinData, CreateSeriesResponseData, FavoriteData, VideoCoinStatusData
from .models import PlayUrlResponseData, VideoPage, VideoView

__all__ = [
    "CoinData",
    "FavoriteData",
    "VideoCoinStatusData",
    "CreateSeriesResponseData",
    "PlayerInfoResponseData",
    "RcmdFeedResponseData",
    "AiSummaryResponseData",
    "GetSeasonsArchivesData",
    "GetSeasonsSeriesData",
    "GetSeriesArchivesData",
    "GetSeriesData",
    "InteractiveVideoInfoResponseData",
    "OnlineTotalResponseData",
    "PlayUrlResponseData",
    "RelatedVideo",
    "VideoDetail",
    "VideoDetailTag",
    "VideoPage",
    "VideoTag",
    "VideoView",
]
