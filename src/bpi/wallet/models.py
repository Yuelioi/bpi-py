from __future__ import annotations

from pydantic import Field

from bpi._core.response import ResponseModel


class UserWallet(ResponseModel):
    mid: int
    total_bp: float = Field(alias="totalBp")
    default_bp: float = Field(alias="defaultBp")
    ios_bp: float = Field(alias="iosBp")
    coupon_balance: float = Field(alias="couponBalance")
    available_bp: float = Field(alias="availableBp")
    unavailable_bp: float = Field(alias="unavailableBp")
    unavailable_reason: str = Field(alias="unavailableReason")
    tip: str
    need_show_class_balance: int = Field(alias="needShowClassBalance")
