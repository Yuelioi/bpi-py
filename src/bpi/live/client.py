from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from .models import (
    BannedUserListData,
    BlindGiftData,
    CreateRoomData,
    EmoticonData,
    FollowUpLiveData,
    GiftTypeItem,
    GuardListData,
    HeartBeatData,
    LiveDanmuInfoData,
    LiveParentArea,
    LiveStreamData,
    LiveWebListData,
    LotteryInfoData,
    MyMedalsData,
    PcLiveVersionData,
    RecommendData,
    ReplayListData,
    RoomGiftData,
    RoomInfoData,
    SendDanmuData,
    ShieldKeywordListData,
    SilentUserListData,
    StartLiveData,
    StopLiveData,
    UpdatePreLiveInfoData,
    UpdateRoomData,
    WebUpStreamAddrData,
)
from .params import (
    heartbeat_query,
    moderation_referer,
    nonblank,
    optional_page_query,
    positive,
    positive_optional,
    room_gift_query,
    stream_query,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_AREAS = TypeAdapter(list[LiveParentArea])
_ROOM = TypeAdapter(RoomInfoData)
_STREAM = TypeAdapter(LiveStreamData)
_RECOMMEND = TypeAdapter(RecommendData)
_VERSION = TypeAdapter(PcLiveVersionData)
_GIFT_TYPES = TypeAdapter(list[GiftTypeItem])
_ROOM_GIFTS = TypeAdapter(RoomGiftData)
_BLIND_GIFT = TypeAdapter(BlindGiftData)
_DANMU_INFO = TypeAdapter(LiveDanmuInfoData)
_EMOTICONS = TypeAdapter(EmoticonData)
_LOTTERY = TypeAdapter(LotteryInfoData)
_MY_MEDALS = TypeAdapter(MyMedalsData)
_FOLLOW_UP = TypeAdapter(FollowUpLiveData)
_FOLLOW_UP_WEB = TypeAdapter(LiveWebListData)
_REPLAY = TypeAdapter(ReplayListData)
_GUARD = TypeAdapter(GuardListData)
_SILENT = TypeAdapter(SilentUserListData)
_BANNED = TypeAdapter(BannedUserListData)
_SHIELD = TypeAdapter(ShieldKeywordListData)
_HEARTBEAT = TypeAdapter(HeartBeatData)
_SEND_DANMU = TypeAdapter(SendDanmuData)
_CREATE_ROOM = TypeAdapter(CreateRoomData)
_UPDATE_ROOM = TypeAdapter(UpdateRoomData)
_UPSTREAM = TypeAdapter(WebUpStreamAddrData)
_START = TypeAdapter(StartLiveData)
_STOP = TypeAdapter(StopLiveData)
_PRELIVE = TypeAdapter(UpdatePreLiveInfoData)
_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class LiveClient:
    """Live room, stream, moderation and broadcaster APIs."""

    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def area_list(self) -> list[LiveParentArea]:
        return await self._client._get_payload(
            "/room/v1/Area/getList", {}, _AREAS, host="api.live.bilibili.com"
        )

    async def room_info(self, *, room_id: int) -> RoomInfoData:
        return await self._client._get_payload(
            "/room/v1/Room/get_info",
            {"room_id": str(positive("room_id", room_id))},
            _ROOM,
            host="api.live.bilibili.com",
        )

    async def stream(
        self,
        *,
        cid: int,
        platform: str | None = None,
        quality: int | None = None,
        qn: int | None = None,
    ) -> LiveStreamData:
        return await self._client._get_payload(
            "/room/v1/Room/playUrl",
            stream_query(cid, platform, quality, qn),
            _STREAM,
            host="api.live.bilibili.com",
        )

    async def recommend(self) -> RecommendData:
        return await self._client._get_payload(
            "/xlive/web-interface/v1/webMain/getMoreRecList",
            {"platform": "web", "web_location": "333.1007"},
            _RECOMMEND,
            host="api.live.bilibili.com",
        )

    async def version(self) -> PcLiveVersionData:
        return await self._client._get_payload(
            "/xlive/app-blink/v1/liveVersionInfo/getHomePageLiveVersion",
            {"system_version": "2"},
            _VERSION,
            host="api.live.bilibili.com",
        )

    async def gift_types(self) -> list[GiftTypeItem]:
        return await self._client._get_payload(
            "/gift/v1/master/getGiftTypes",
            {},
            _GIFT_TYPES,
            host="api.live.bilibili.com",
        )

    async def room_gift_list(
        self,
        *,
        room_id: int,
        area_parent_id: int | None = None,
        area_id: int | None = None,
    ) -> RoomGiftData:
        return await self._client._get_payload(
            "/xlive/web-room/v1/giftPanel/roomGiftList",
            room_gift_query(room_id, area_parent_id, area_id),
            _ROOM_GIFTS,
            host="api.live.bilibili.com",
        )

    async def blind_gift_info(self, *, gift_id: int) -> BlindGiftData:
        return await self._client._get_payload(
            "/xlive/general-interface/v1/blindFirstWin/getInfo",
            {"gift_id": str(positive("gift_id", gift_id))},
            _BLIND_GIFT,
            host="api.live.bilibili.com",
        )

    async def danmu_info(self, *, room_id: int, info_type: int = 0) -> LiveDanmuInfoData:
        room_id = positive("room_id", room_id)
        if type(info_type) is not int or info_type < 0 or info_type > 255:
            from bpi.errors import InvalidParameterError

            raise InvalidParameterError("info_type must fit u8")
        params = await self._client._sign({"id": str(room_id), "type": str(info_type)})
        return await self._client._get_payload(
            "/xlive/web-room/v1/index/getDanmuInfo",
            params,
            _DANMU_INFO,
            host="api.live.bilibili.com",
        )

    async def emoticons(self, *, room_id: int, platform: str = "pc") -> EmoticonData:
        return await self._client._get_payload(
            "/xlive/web-ucenter/v2/emoticon/GetEmoticons",
            {
                "room_id": str(positive("room_id", room_id)),
                "platform": nonblank("platform", platform),
            },
            _EMOTICONS,
            host="api.live.bilibili.com",
        )

    async def lottery_info(self, *, room_id: int) -> LotteryInfoData:
        params = await self._client._sign({"roomid": str(positive("room_id", room_id))})
        return await self._client._get_payload(
            "/xlive/lottery-interface/v1/lottery/getLotteryInfoWeb",
            params,
            _LOTTERY,
            host="api.live.bilibili.com",
        )

    async def my_medals(self, *, page: int = 1, page_size: int = 10) -> MyMedalsData:
        return await self._client._get_payload(
            "/xlive/app-ucenter/v1/user/GetMyMedals",
            {
                "page": str(positive("page", page)),
                "page_size": str(positive("page_size", page_size)),
            },
            _MY_MEDALS,
            host="api.live.bilibili.com",
        )

    async def follow_up_list(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        ignore_record: int | None = None,
        hit_ab: bool | None = None,
    ) -> FollowUpLiveData:
        params = optional_page_query(page, page_size)
        if ignore_record is not None:
            if type(ignore_record) is not int or ignore_record not in (0, 1):
                from bpi.errors import InvalidParameterError

                raise InvalidParameterError("ignore_record must be 0 or 1")
            params["ignoreRecord"] = str(ignore_record)
        if hit_ab is not None:
            if type(hit_ab) is not bool:
                from bpi.errors import InvalidParameterError

                raise InvalidParameterError("hit_ab must be bool")
            params["hit_ab"] = "true" if hit_ab else "false"
        return await self._client._get_payload(
            "/xlive/web-ucenter/user/following",
            params,
            _FOLLOW_UP,
            host="api.live.bilibili.com",
        )

    async def follow_up_web_list(self, *, hit_ab: bool | None = None) -> LiveWebListData:
        params: dict[str, str] = {}
        if hit_ab is not None:
            if type(hit_ab) is not bool:
                from bpi.errors import InvalidParameterError

                raise InvalidParameterError("hit_ab must be bool")
            params["hit_ab"] = "true" if hit_ab else "false"
        return await self._client._get_payload(
            "/xlive/web-ucenter/v1/xfetter/GetWebList",
            params,
            _FOLLOW_UP_WEB,
            host="api.live.bilibili.com",
        )

    async def replay_list(
        self, *, page: int | None = None, page_size: int | None = None
    ) -> ReplayListData:
        return await self._client._get_payload(
            "/xlive/app-blink/v1/anchorVideo/AnchorGetReplayList",
            optional_page_query(page, page_size),
            _REPLAY,
            host="api.live.bilibili.com",
        )

    async def guard_list(
        self,
        *,
        room_id: int,
        ruid: int,
        page: int = 1,
        page_size: int = 20,
        typ: int = 5,
    ) -> GuardListData:
        params = {
            "roomid": str(positive("room_id", room_id)),
            "ruid": str(positive("ruid", ruid)),
            "page": str(positive("page", page)),
            "page_size": str(positive("page_size", page_size)),
            "typ": str(positive("typ", typ)),
        }
        return await self._client._get_payload(
            "/xlive/app-room/v2/guardTab/topListNew",
            params,
            _GUARD,
            host="api.live.bilibili.com",
        )

    async def silent_users(
        self, *, room_id: int, page: int = 1, page_size: int = 10
    ) -> SilentUserListData:
        referer = moderation_referer(room_id)
        csrf = self._client._csrf(host="api.live.bilibili.com", optional=True)
        form = {
            "room_id": str(room_id),
            "pn": str(positive("page", page)),
            "ps": str(positive("page_size", page_size)),
            "csrf_token": csrf,
            "csrf": csrf,
        }
        return await self._client._post_payload(
            "/xlive/web-ucenter/v1/banned/GetSilentUserList",
            {},
            _SILENT,
            form=form,
            host="api.live.bilibili.com",
            referer=referer,
        )

    async def banned_users(
        self,
        *,
        room_id: int,
        anchor_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> BannedUserListData:
        referer = moderation_referer(room_id)
        csrf = self._client._csrf(host="api.live.bilibili.com", optional=True)
        params = {
            "anchor_id": str(positive("anchor_id", anchor_id)),
            "pn": str(positive("page", page)),
            "ps": str(positive("page_size", page_size)),
            "mobi_app": "android",
            "platform": "android",
            "spmid": "444.8.0.0",
            "csrf_token": csrf,
            "csrf": csrf,
            "visit_id": "",
        }
        return await self._client._get_payload(
            "/xlive/app-ucenter/v2/xbanned/banned/GetBlackList",
            params,
            _BANNED,
            host="api.live.bilibili.com",
            referer=referer,
        )

    async def shield_keywords(self, *, room_id: int) -> ShieldKeywordListData:
        referer = moderation_referer(room_id)
        csrf = self._client._csrf(host="api.live.bilibili.com", optional=True)
        form = {
            "room_id": str(room_id),
            "spmid": "444.8.0.0",
            "csrf_token": csrf,
            "csrf": csrf,
            "visit_id": "",
            "mobi_app": "android",
            "platform": "android",
        }
        return await self._client._post_payload(
            "/xlive/app-ucenter/v1/banned/GetShieldKeywordList",
            {},
            _SHIELD,
            form=form,
            host="api.live.bilibili.com",
            referer=referer,
        )

    async def web_heart_beat(
        self, *, room_id: int, next_interval: int = 60, platform: str = "web"
    ) -> HeartBeatData:
        return await self._client._get_payload(
            "/xlive/rdata-interface/v1/heartbeat/webHeartBeat",
            heartbeat_query(room_id, next_interval, platform),
            _HEARTBEAT,
            host="live-trace.bilibili.com",
        )

    async def live_send_danmu(
        self,
        *,
        room_id: int,
        message: str,
        color: int = 16777215,
        font_size: int = 25,
    ) -> SendDanmuData:
        room_id = positive("room_id", room_id)
        message = nonblank("message", message)
        if type(color) is not int or color < 0:
            from bpi.errors import InvalidParameterError

            raise InvalidParameterError("color must be non-negative")
        if type(font_size) is not int or font_size < 0:
            from bpi.errors import InvalidParameterError

            raise InvalidParameterError("font_size must be non-negative")
        csrf = self._client.csrf()
        form = {
            "csrf": csrf,
            "roomid": str(room_id),
            "msg": message,
            "rnd": str(int(self._client._clock())),
            "bubble": "0",
            "mode": "1",
            "statistics": '{"appId":100,"platform":5}',
            "csrf_token": csrf,
            "color": str(color),
            "fontsize": str(font_size),
        }
        return await self._client._post_payload(
            "/msg/send",
            {},
            _SEND_DANMU,
            form=form,
            multipart=True,
            host="api.live.bilibili.com",
        )

    async def live_create_room(self) -> CreateRoomData:
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/xlive/app-blink/v1/preLive/CreateRoom",
            {},
            _CREATE_ROOM,
            form={"platform": "web", "visit_id": "", "csrf": csrf, "csrf_token": csrf},
            multipart=True,
            host="api.live.bilibili.com",
        )

    async def live_update_room_info(
        self,
        *,
        room_id: int,
        title: str | None = None,
        area_id: int | None = None,
        add_tag: str | None = None,
        del_tag: str | None = None,
    ) -> UpdateRoomData:
        csrf = self._client.csrf()
        form = {"room_id": str(positive("room_id", room_id)), "csrf": csrf, "csrf_token": csrf}
        area_id = positive_optional("area_id", area_id)
        if title is not None:
            form["title"] = title
        if area_id is not None:
            form["area_id"] = str(area_id)
        if add_tag is not None:
            form["add_tag"] = add_tag
        if del_tag is not None:
            form["del_tag"] = del_tag
        return await self._client._post_payload(
            "/room/v1/Room/update",
            {},
            _UPDATE_ROOM,
            form=form,
            multipart=True,
            host="api.live.bilibili.com",
        )

    async def live_fetch_web_up_stream_addr(self) -> WebUpStreamAddrData:
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/xlive/app-blink/v1/live/FetchWebUpStreamAddr",
            {},
            _UPSTREAM,
            form={"platform": "pc", "backup_stream": "0", "csrf": csrf, "csrf_token": csrf},
            host="api.live.bilibili.com",
        )

    async def live_web_center_start(self, *, room_id: int, area_v2: int) -> StartLiveData:
        csrf = self._client.csrf()
        params = await self._client._sign(
            {
                "room_id": str(positive("room_id", room_id)),
                "platform": "pc",
                "area_v2": str(positive("area_v2", area_v2)),
                "backup_stream": "0",
                "csrf": csrf,
                "csrf_token": csrf,
            }
        )
        return await self._client._post_payload(
            "/xlive/app-blink/v1/streaming/WebLiveCenterStartLive",
            params,
            _START,
            host="api.live.bilibili.com",
        )

    async def live_stop(self, *, room_id: int, platform: str) -> StopLiveData:
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/room/v1/Room/stopLive",
            {},
            _STOP,
            form={
                "platform": nonblank("platform", platform),
                "room_id": str(positive("room_id", room_id)),
                "csrf": csrf,
                "csrf_token": csrf,
            },
            multipart=True,
            host="api.live.bilibili.com",
        )

    async def live_update_pre_live_info(
        self, *, title: str | None = None, cover: str | None = None
    ) -> UpdatePreLiveInfoData:
        csrf = self._client.csrf()
        form = {
            "platform": "web",
            "mobi_app": "web",
            "build": "1",
            "csrf": csrf,
            "csrf_token": csrf,
        }
        if title is not None:
            form["title"] = title
        if cover is not None:
            form["cover"] = cover
        return await self._client._post_payload(
            "/xlive/app-blink/v1/preLive/UpdatePreLiveInfo",
            {},
            _PRELIVE,
            form=form,
            multipart=True,
            host="api.live.bilibili.com",
        )

    async def live_update_room_news(self, *, room_id: int, uid: int, content: str) -> JsonValue:
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/xlive/app-blink/v1/index/updateRoomNews",
            {},
            _JSON,
            form={
                "room_id": str(positive("room_id", room_id)),
                "uid": str(positive("uid", uid)),
                "content": content,
                "csrf": csrf,
                "csrf_token": csrf,
            },
            multipart=True,
            host="api.live.bilibili.com",
        )

    async def live_add_silent_user(
        self, *, room_id: int, tuid: int, hour: int, msg: str | None = None
    ) -> JsonValue:
        room_id = positive("room_id", room_id)
        tuid = positive("tuid", tuid)
        if type(hour) is not int or hour < -1:
            from bpi.errors import InvalidParameterError

            raise InvalidParameterError("hour must be -1, 0, or positive")
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/xlive/web-ucenter/v1/banned/AddSilentUser",
            {},
            _JSON,
            form={
                "room_id": str(room_id),
                "tuid": str(tuid),
                "msg": msg or "",
                "mobile_app": "web",
                "type": "2" if hour == 0 else "1",
                "hour": str(hour),
                "csrf_token": csrf,
                "csrf": csrf,
            },
            optional=True,
            host="api.live.bilibili.com",
        )

    async def live_del_block_user(self, *, room_id: int, tuid: int) -> JsonValue:
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/xlive/web-ucenter/v1/banned/DelSilentUser",
            {},
            _JSON,
            form={
                "room_id": str(positive("room_id", room_id)),
                "tuid": str(positive("tuid", tuid)),
                "csrf_token": csrf,
                "csrf": csrf,
            },
            optional=True,
            host="api.live.bilibili.com",
        )

    async def live_add_banned_user(self, *, room_id: int, anchor_id: int, tuid: int) -> JsonValue:
        referer = moderation_referer(room_id)
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/xlive/app-ucenter/v2/xbanned/banned/AddBlack",
            {},
            _JSON,
            form={
                "tuid": str(positive("tuid", tuid)),
                "anchor_id": str(positive("anchor_id", anchor_id)),
                "spmid": "444.8.0.0",
                "csrf_token": csrf,
                "csrf": csrf,
                "visit_id": "",
            },
            optional=True,
            host="api.live.bilibili.com",
            referer=referer,
        )

    async def live_del_banned_user(self, *, room_id: int, anchor_id: int, tuid: int) -> JsonValue:
        referer = moderation_referer(room_id)
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/xlive/app-ucenter/v2/xbanned/banned/DelBlack",
            {},
            _JSON,
            form={
                "tuid": str(positive("tuid", tuid)),
                "anchor_id": str(positive("anchor_id", anchor_id)),
                "spmid": "444.8.0.0",
                "csrf_token": csrf,
                "csrf": csrf,
                "visit_id": "",
                "mobi_app": "android",
                "platform": "android",
            },
            optional=True,
            host="api.live.bilibili.com",
            referer=referer,
        )

    async def live_add_shield_keyword(self, *, room_id: int, keyword: str) -> JsonValue:
        return await self._shield_keyword_write(
            "/xlive/app-ucenter/v1/banned/AddShieldKeyword", room_id, keyword
        )

    async def live_del_shield_keyword(self, *, room_id: int, keyword: str) -> JsonValue:
        return await self._shield_keyword_write(
            "/xlive/app-ucenter/v1/banned/DelShieldKeyword", room_id, keyword
        )

    async def _shield_keyword_write(self, path: str, room_id: int, keyword: str) -> JsonValue:
        room_id = positive("room_id", room_id)
        keyword = nonblank("keyword", keyword)
        csrf = self._client.csrf()
        return await self._client._post_payload(
            path,
            {},
            _JSON,
            form={
                "keyword": keyword,
                "room_id": str(room_id),
                "spmid": "444.8.0.0",
                "csrf_token": csrf,
                "csrf": csrf,
                "visit_id": "",
                "mobi_app": "android",
                "platform": "android",
            },
            optional=True,
            host="api.live.bilibili.com",
        )
