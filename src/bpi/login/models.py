from __future__ import annotations

import builtins

from pydantic import Field, field_validator

from bpi._core.response import ResponseModel


class LoginWbiImg(ResponseModel):
    img_url: str
    sub_url: str


class LoginNav(ResponseModel):
    is_login: bool = Field(alias="isLogin")
    mid: int | None = None
    uname: str | None = None
    face: str | None = None
    wbi_img: LoginWbiImg

    @field_validator("mid", mode="before")
    @classmethod
    def anonymous_mid(cls, value: object) -> object:
        return None if type(value) is int and value == 0 else value

    @field_validator("uname", "face", mode="before")
    @classmethod
    def anonymous_string(cls, value: object) -> object:
        return None if value == "" else value


class LoginCoinBalance(ResponseModel):
    money: float


class LoginNoticeData(ResponseModel):
    mid: int
    device_name: str
    login_type: str
    login_time: str
    location: str
    ip: str


class LoginLogEntry(ResponseModel):
    ip: str
    time: int
    time_at: str
    status: bool
    login_type: int = Field(alias="type")
    location: str = Field(alias="geo")


class LoginLogData(ResponseModel):
    count: int
    list: builtins.list[LoginLogEntry]


class Geetest(ResponseModel):
    challenge: str
    gt: str


class TencentCaptcha(ResponseModel):
    appid: str


class GeetestData(ResponseModel):
    type_field: str = Field(alias="type")
    token: str
    geetest: Geetest
    tencent: TencentCaptcha


class GenerateCaptcha(ResponseModel):
    token: str
    gt: str
    challenge: str


class GenerateQrCodeData(ResponseModel):
    url: str
    qrcode_key: str


class CheckQrCodeStatusData(ResponseModel):
    url: str
    refresh_token: str
    timestamp: int
    code: int
    message: str
    cookies: builtins.list[tuple[str, str]] = Field(default_factory=builtins.list)


class LogoutData(ResponseModel):
    redirect_url: str = Field(alias="redirectUrl")


class SmsSendData(ResponseModel):
    captcha_key: str


class SmsLoginData(ResponseModel):
    is_new: bool
    status: int
    url: str
