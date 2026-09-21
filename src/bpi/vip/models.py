from __future__ import annotations

from pydantic import AliasChoices, Field, field_validator

from bpi._core.response import ResponseModel


def _numeric_string(value: object) -> object:
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


class Account(ResponseModel):
    mid: int
    name: str
    sex: str
    face: str
    sign: str
    rank: int
    birthday: int
    is_fake_account: int
    is_deleted: int
    in_reg_audit: int
    is_senior_member: int


class VipLabel(ResponseModel):
    text: str = ""
    label_theme: str = ""
    text_color: str = ""
    bg_style: int = 0
    bg_color: str = ""


class Vip(ResponseModel):
    vip_type: int = Field(validation_alias=AliasChoices("vip_type", "vipType", "type"))
    vip_status: int = Field(validation_alias=AliasChoices("vip_status", "vipStatus", "status"))
    vip_due_date: int = Field(
        default=0,
        validation_alias=AliasChoices("vip_due_date", "vipDueDate", "due_date"),
    )
    label: VipLabel = Field(default_factory=VipLabel)
    nickname_color: str = ""
    vip_pay_type: int | None = None
    role: int | None = None
    is_tv_vip: bool | None = None
    tv_vip_status: int | None = None
    tv_vip_pay_type: int | None = None
    tv_due_date: int | None = None
    mid: int | None = None
    name: str | None = None

    @field_validator(
        "vip_type",
        "vip_status",
        "vip_due_date",
        "vip_pay_type",
        "role",
        "tv_vip_status",
        "tv_vip_pay_type",
        "tv_due_date",
        "mid",
        mode="before",
    )
    @classmethod
    def numeric_strings_are_supported(cls, value: object) -> object:
        return _numeric_string(value)


class TvVipInfo(ResponseModel):
    tv_type: int = Field(alias="type")
    vip_pay_type: int
    status: int
    due_date: int


class VipCenterUser(ResponseModel):
    account: Account | None
    vip: Vip | None
    tv: TvVipInfo | None
    background_image_small: str
    background_image_big: str
    panel_title: str
    vip_overdue_explain: str
    tv_overdue_explain: str
    account_exception_text: str
    is_auto_renew: bool
    is_tv_auto_renew: bool
    surplus_seconds: int
    vip_keep_time: int


class WalletInfo(ResponseModel):
    coupon: int
    point: int
    privilege_received: bool


class VipCenterData(ResponseModel):
    user: VipCenterUser
    wallet: WalletInfo
    in_review: bool


class VipExperienceData(ResponseModel):
    type: int
    is_grant: bool
