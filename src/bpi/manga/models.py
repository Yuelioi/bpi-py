from __future__ import annotations

import builtins

from pydantic import Field

from bpi._core.response import ResponseModel


class SeasonTask(ResponseModel):
    id: str = ""
    title: str = ""


class SeasonWelfare(ResponseModel):
    id: str = ""
    title: str = ""


class SeasonText(ResponseModel):
    title: str = ""


class SeasonRank(ResponseModel):
    pass


class SeasonInfoData(ResponseModel):
    current_time: str
    start_time: str
    end_time: str
    remain_amount: int
    season_id: str
    tasks: builtins.list[SeasonTask]
    welfare: builtins.list[SeasonWelfare]
    cover: str
    today_tasks: builtins.list[SeasonTask]
    text: SeasonText | None = None
    season_title: str
    rank: SeasonRank | None = None


class PointInfo(ResponseModel):
    point: int
    origin_point: int
    is_activity: bool
    title: str


class ClockInInfoData(ResponseModel):
    day_count: int
    status: int
    points: builtins.list[int]
    credit_icon: str
    sign_before_icon: str
    sign_today_icon: str
    breathe_icon: str
    new_credit_x_icon: str = ""
    coupon_pic: str = ""
    point_infos: builtins.list[PointInfo]


class UserPointData(ResponseModel):
    point: str


class ProductLimit(ResponseModel):
    limit_type: int = Field(alias="type")
    id: int
    title: str


class Product(ResponseModel):
    id: int
    type: int
    title: str
    image: str
    amount: int
    cost: int
    real_cost: int
    remain_amount: int
    comic_id: int
    limits: builtins.list[ProductLimit]
    discount: int
    product_type: int
    pendant_url: str
    pendant_expire: int
    exchange_limit: int
    address_deadline: str
    act_type: int
    has_exchanged: bool
    main_coupon_deadline: str
    deadline: str
    point: str


class UserCoupon(ResponseModel):
    id: int = Field(alias="ID")
    remain_amount: int
    total_amount: int


class CouponInfo(ResponseModel):
    remain_coupon: int
    remain_silver: int
    remain_shop_coupon: int


class CouponsData(ResponseModel):
    total_remain_amount: int
    user_coupons: builtins.list[UserCoupon]
    coupon_info: CouponInfo


class ShareComicData(ResponseModel):
    point: int
