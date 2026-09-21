from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from .models import (
    ClockInInfoData,
    CouponsData,
    Product,
    SeasonInfoData,
    ShareComicData,
    UserPointData,
)
from .params import (
    buy_episode_body,
    clock_in_makeup_body,
    coupons_body,
    platform_form,
    point_exchange_form,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_SEASON_INFO = TypeAdapter(SeasonInfoData)
_CLOCK_IN_INFO = TypeAdapter(ClockInInfoData)
_USER_POINT = TypeAdapter(UserPointData)
_PRODUCTS = TypeAdapter(list[Product])
_COUPONS = TypeAdapter(CouponsData)
_SHARE_COMIC = TypeAdapter(ShareComicData)
_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class MangaClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def season_info(self) -> SeasonInfoData:
        return await self._client._post_payload(
            "/twirp/user.v1.Season/GetSeasonInfo",
            {},
            _SEASON_INFO,
            host="manga.bilibili.com",
        )

    async def clock_in_info(self) -> ClockInInfoData:
        return await self._client._post_payload(
            "/twirp/activity.v1.Activity/GetClockInInfo",
            {},
            _CLOCK_IN_INFO,
            host="manga.bilibili.com",
        )

    async def user_point(self) -> UserPointData:
        return await self._client._post_payload(
            "/twirp/pointshop.v1.Pointshop/GetUserPoint",
            {},
            _USER_POINT,
            host="manga.bilibili.com",
        )

    async def point_products(self) -> list[Product]:
        return await self._client._post_payload(
            "/twirp/pointshop.v1.Pointshop/ListProduct",
            {},
            _PRODUCTS,
            host="manga.bilibili.com",
        )

    async def coupons(self, *, page_num: int, page_size: int) -> CouponsData:
        return await self._client._post_json_payload(
            "/twirp/user.v1.User/GetCoupons",
            {},
            _COUPONS,
            json_body=coupons_body(page_num, page_size),
            host="manga.bilibili.com",
        )

    async def manga_clock_in(self) -> JsonValue:
        return await self._client._post_payload(
            "/twirp/activity.v1.Activity/ClockIn",
            {},
            _JSON,
            form=platform_form(),
            optional=True,
            host="manga.bilibili.com",
        )

    async def manga_clock_in_makeup(self, *, date: str) -> JsonValue:
        return await self._client._post_json_payload(
            "/twirp/activity.v1.Activity/ClockIn",
            {"platform": "android"},
            _JSON,
            json_body=clock_in_makeup_body(date),
            optional=True,
            host="manga.bilibili.com",
        )

    async def manga_share_comic(self) -> ShareComicData:
        return await self._client._post_payload(
            "/twirp/activity.v1.Activity/ShareComic",
            {},
            _SHARE_COMIC,
            form=platform_form(),
            host="manga.bilibili.com",
        )

    async def manga_buy_episode(
        self,
        *,
        ep_id: int,
        buy_method: int,
        coupon_id: int,
        comic_id: int | None = None,
        auto_pay_gold_status: int | None = None,
        is_presale: int | None = None,
        pay_amount: int | None = None,
    ) -> JsonValue:
        return await self._client._post_json_payload(
            "/twirp/comic.v1.Comic/BuyEpisode",
            {"platform": "web"},
            _JSON,
            json_body=buy_episode_body(
                ep_id,
                buy_method,
                coupon_id,
                comic_id=comic_id,
                auto_pay_gold_status=auto_pay_gold_status,
                is_presale=is_presale,
                pay_amount=pay_amount,
            ),
            optional=True,
            host="manga.bilibili.com",
        )

    async def manga_buy_episode_with_coupon(self, *, ep_id: int, coupon_id: int) -> JsonValue:
        return await self.manga_buy_episode(
            ep_id=ep_id,
            buy_method=2,
            coupon_id=coupon_id,
            auto_pay_gold_status=2,
            is_presale=0,
        )

    async def manga_buy_episode_with_free(self, *, comic_id: int, ep_id: int) -> JsonValue:
        return await self.manga_buy_episode(
            ep_id=ep_id,
            buy_method=4,
            coupon_id=0,
            comic_id=comic_id,
        )

    async def manga_buy_episode_with_general_coupon(
        self, *, ep_id: int, pay_amount: int
    ) -> JsonValue:
        return await self.manga_buy_episode(
            ep_id=ep_id,
            buy_method=5,
            coupon_id=0,
            auto_pay_gold_status=2,
            is_presale=0,
            pay_amount=pay_amount,
        )

    async def manga_point_exchange(
        self, *, product_id: int, product_num: int, point: int
    ) -> JsonValue:
        return await self._client._post_payload(
            "/twirp/pointshop.v1.Pointshop/Exchange",
            {},
            _JSON,
            form=point_exchange_form(product_id, product_num, point),
            optional=True,
            host="manga.bilibili.com",
        )
