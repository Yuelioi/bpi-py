from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from bpi.errors import InvalidParameterError

from .models import (
    CreateComplexDynamicData,
    CreateDynamicData,
    DynamicAllData,
    DynamicBannerData,
    DynamicContentItem,
    DynamicCreatePic,
    DynamicDetailData,
    DynamicForwardData,
    DynamicForwardInfoData,
    DynamicLotteryData,
    DynamicNavData,
    DynamicPic,
    DynamicReactionData,
    DynamicTopic,
    DynamicUpdateData,
    DynUpUsersData,
    LiveUsersData,
    RecentUpData,
    UploadPicData,
)
from .params import (
    DEFAULT_ALL_FEATURES,
    DEFAULT_ALL_WEB_LOCATION,
    DEFAULT_DETAIL_FEATURES,
    all_query,
    check_new_query,
    complex_body,
    delete_draft_form,
    detail_query,
    id_query,
    like_body,
    live_users_query,
    lottery_query,
    nav_feed_query,
    offset_query,
    text_content,
    top_body,
    up_users_query,
    upload_category,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_ALL = TypeAdapter(DynamicAllData)
_UPDATE = TypeAdapter(DynamicUpdateData)
_NAV = TypeAdapter(DynamicNavData)
_BANNER = TypeAdapter(DynamicBannerData)
_DETAIL = TypeAdapter(DynamicDetailData)
_REACTIONS = TypeAdapter(DynamicReactionData)
_LOTTERY = TypeAdapter(DynamicLotteryData)
_FORWARDS = TypeAdapter(DynamicForwardData)
_PICS = TypeAdapter(list[DynamicPic])
_FORWARD_ITEM = TypeAdapter(DynamicForwardInfoData)
_LIVE_USERS = TypeAdapter(LiveUsersData)
_UP_USERS = TypeAdapter(DynUpUsersData)
_RECENT_UP = TypeAdapter(RecentUpData)
_UPLOAD = TypeAdapter(UploadPicData)
_CREATE_TEXT = TypeAdapter(CreateDynamicData)
_CREATE_COMPLEX = TypeAdapter(CreateComplexDynamicData)
_OPTIONAL_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class DynamicClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def all(
        self,
        *,
        features: str = DEFAULT_ALL_FEATURES,
        web_location: str = DEFAULT_ALL_WEB_LOCATION,
        host_mid: int | None = None,
        offset: str | None = None,
        update_baseline: str | None = None,
    ) -> DynamicAllData:
        params = all_query(
            features=features,
            web_location=web_location,
            host_mid=host_mid,
            offset=offset,
            update_baseline=update_baseline,
        )
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/feed/all", params, _ALL
        )

    async def check_new(
        self, *, update_baseline: str, dynamic_type: str | None = None
    ) -> DynamicUpdateData:
        params = check_new_query(update_baseline, dynamic_type=dynamic_type)
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/feed/all/update", params, _UPDATE
        )

    async def nav_feed(
        self, *, update_baseline: str | None = None, offset: str | None = None
    ) -> DynamicNavData:
        params = nav_feed_query(update_baseline=update_baseline, offset=offset)
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/feed/nav", params, _NAV
        )

    async def feed_banner(self) -> DynamicBannerData:
        params = {"platform": "1", "position": "web动态", "web_location": "333.1365"}
        return await self._client._get_payload("/x/dynamic/feed/dyn/banner", params, _BANNER)

    async def detail(
        self, *, dynamic_id: str, features: str = DEFAULT_DETAIL_FEATURES
    ) -> DynamicDetailData:
        params = detail_query(dynamic_id, features=features)
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/detail", params, _DETAIL
        )

    async def reactions(
        self, *, dynamic_id: str, offset: str | None = None
    ) -> DynamicReactionData:
        params = offset_query(dynamic_id, offset=offset)
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/detail/reaction", params, _REACTIONS
        )

    async def lottery_notice(self, *, business_id: str) -> DynamicLotteryData:
        params = lottery_query(business_id, csrf="")
        params["csrf"] = self._client.csrf()
        return await self._client._get_payload(
            "/lottery_svr/v1/lottery_svr/lottery_notice",
            params,
            _LOTTERY,
            host="api.vc.bilibili.com",
        )

    async def forwards(
        self, *, dynamic_id: str, offset: str | None = None
    ) -> DynamicForwardData:
        params = offset_query(dynamic_id, offset=offset)
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/detail/forward", params, _FORWARDS
        )

    async def pics(self, *, dynamic_id: str) -> list[DynamicPic]:
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/detail/pic", id_query(dynamic_id), _PICS
        )

    async def forward_item(self, *, dynamic_id: str) -> DynamicForwardInfoData:
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/detail/forward/item",
            id_query(dynamic_id),
            _FORWARD_ITEM,
        )

    async def live_users(self, *, size: int | None = None) -> LiveUsersData:
        return await self._client._get_payload(
            "/dynamic_svr/v1/dynamic_svr/w_live_users",
            live_users_query(size=size),
            _LIVE_USERS,
            host="api.vc.bilibili.com",
        )

    async def up_users(self, *, teenagers_mode: bool = False) -> DynUpUsersData:
        return await self._client._get_payload(
            "/dynamic_svr/v1/dynamic_svr/w_dyn_uplist",
            up_users_query(teenagers_mode=teenagers_mode),
            _UP_USERS,
            host="api.vc.bilibili.com",
        )

    async def recent_up(self) -> RecentUpData:
        return await self._client._get_payload(
            "/x/polymer/web-dynamic/v1/portal", {}, _RECENT_UP
        )

    async def like(self, *, dyn_id_str: str, up: int) -> JsonValue:
        body = like_body(dyn_id_str, up)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x/dynamic/feed/dyn/thumb",
            {"csrf": csrf},
            _OPTIONAL_JSON,
            json_body=body,
            optional=True,
        )

    async def delete_draft(self, *, draft_id: str) -> JsonValue:
        form = delete_draft_form(draft_id, csrf="")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/dynamic_draft/v1/dynamic_draft/rm_draft",
            {},
            _OPTIONAL_JSON,
            form=form,
            optional=True,
            host="api.vc.bilibili.com",
        )

    async def set_top(self, *, dyn_str: str) -> JsonValue:
        body = top_body(dyn_str)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x/dynamic/feed/space/set_top",
            {"csrf": csrf},
            _OPTIONAL_JSON,
            json_body=body,
            optional=True,
        )

    async def remove_top(self, *, dyn_str: str) -> JsonValue:
        body = top_body(dyn_str)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x/dynamic/feed/space/rm_top",
            {"csrf": csrf},
            _OPTIONAL_JSON,
            json_body=body,
            optional=True,
        )

    async def upload_pic(
        self, *, file_path: str | Path, category: str = "daily"
    ) -> UploadPicData:
        category = upload_category(category)
        path = Path(file_path)
        try:
            body = path.read_bytes()
        except OSError:
            raise InvalidParameterError("file_path must point to a readable file") from None
        if not path.name:
            raise InvalidParameterError("file_path must include a file name")
        csrf = self._client.csrf()
        return await self._client._post_multipart_payload(
            "/x/dynamic/feed/draw/upload_bfs",
            {},
            _UPLOAD,
            form={"csrf": csrf, "category": category, "biz": "new_dyn"},
            file_part=("file_up", path.name, body, "image/jpeg"),
        )

    async def create_text(self, *, content: str) -> CreateDynamicData:
        content = text_content(content)
        csrf = self._client.csrf()
        return await self._client._post_multipart_payload(
            "/dynamic_svr/v1/dynamic_svr/create",
            {},
            _CREATE_TEXT,
            form={
                "dynamic_id": "0",
                "type": "4",
                "rid": "0",
                "content": content,
                "csrf": csrf,
                "csrf_token": csrf,
            },
            host="api.vc.bilibili.com",
        )

    async def create_complex(
        self,
        *,
        scene: int,
        contents: Sequence[DynamicContentItem],
        pics: Sequence[DynamicCreatePic] | None = None,
        topic: DynamicTopic | None = None,
    ) -> CreateComplexDynamicData:
        body = complex_body(scene, contents, pics=pics, topic=topic)
        csrf = self._client.csrf()
        return await self._client._post_json_payload(
            "/x/dynamic/feed/create/dyn",
            {"csrf": csrf},
            _CREATE_COMPLEX,
            json_body=body,
        )
