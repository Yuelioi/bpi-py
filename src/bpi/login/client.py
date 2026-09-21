from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from bpi._core.response import decode_payload
from bpi._generated.login_client import LoginReadMethods
from bpi.login.models import (
    CheckQrCodeStatusData,
    GeetestData,
    GenerateCaptcha,
    GenerateQrCodeData,
    LoginCoinBalance,
    LoginLogData,
    LoginNav,
    LoginNoticeData,
    LogoutData,
    SmsLoginData,
    SmsSendData,
)
from bpi.login.params import (
    log_query,
    logout_form,
    notice_query,
    qr_poll_query,
    sms_code_form,
    sms_login_form,
    user_sign_form,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient

NAV = TypeAdapter(LoginNav)
COIN = TypeAdapter(LoginCoinBalance)
TODAY_COIN_EXP = TypeAdapter(int)
NOTICE = TypeAdapter(LoginNoticeData)
LOG = TypeAdapter(LoginLogData)
GEETEST = TypeAdapter(GeetestData)
QR_GENERATE = TypeAdapter(GenerateQrCodeData)
QR_POLL = TypeAdapter(CheckQrCodeStatusData)
LOGOUT = TypeAdapter(LogoutData)
SMS_SEND = TypeAdapter(SmsSendData)
SMS_LOGIN = TypeAdapter(SmsLoginData)
OPTIONAL_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class LoginClient(LoginReadMethods):
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def nav(self) -> LoginNav:
        """Get login state. Anonymous API code -101 raises AuthenticationError."""
        return await self._client._get_payload("/x/web-interface/nav", {}, NAV)

    async def coin(self) -> LoginCoinBalance:
        return await self._client._get_payload(
            "/site/getCoin", {}, COIN, host="account.bilibili.com"
        )

    async def today_coin_exp(self) -> int:
        return await self._client._get_payload(
            "/x/web-interface/coin/today/exp", {}, TODAY_COIN_EXP
        )

    async def notice(self, *, mid: int, buvid: str | None = None) -> LoginNoticeData:
        return await self._client._get_payload(
            "/x/safecenter/login_notice", notice_query(mid, buvid), NOTICE
        )

    async def log(
        self, *, jsonp: str = "jsonp", web_location: str = "333.33"
    ) -> LoginLogData:
        return await self._client._get_payload(
            "/x/member/web/login/log", log_query(jsonp, web_location), LOG
        )

    async def generate_captcha(self) -> GenerateCaptcha:
        data = await self._client._get_payload(
            "/x/passport-login/captcha",
            {"source": "main_web"},
            GEETEST,
            host="passport.bilibili.com",
        )
        return GenerateCaptcha(
            token=data.token,
            gt=data.geetest.gt,
            challenge=data.geetest.challenge,
        )

    async def qr_generate(self) -> GenerateQrCodeData:
        return await self._client._get_payload(
            "/x/passport-login/web/qrcode/generate",
            {},
            QR_GENERATE,
            host="passport.bilibili.com",
        )

    async def qr_poll(self, *, qrcode_key: str) -> CheckQrCodeStatusData:
        response = await self._client._send_response(
            "GET",
            "/x/passport-login/web/qrcode/poll",
            qr_poll_query(qrcode_key),
            host="passport.bilibili.com",
        )
        data = decode_payload(response.content, QR_POLL)
        if data.code == 0:
            cookies = list(response.cookies.items())
            if cookies:
                data = data.model_copy(update={"cookies": cookies})
        return data

    async def logout(self, *, gourl: str = "javascript:history.go(-1)") -> LogoutData:
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/login/exit/v2",
            {},
            LOGOUT,
            form=logout_form(csrf, gourl),
            host="passport.bilibili.com",
        )

    async def send_sms_code(
        self,
        *,
        cid: int,
        tel: str,
        token: str,
        challenge: str,
        validate: str,
        seccode: str,
        source: str = "main_web",
    ) -> SmsSendData:
        form = sms_code_form(
            cid,
            tel,
            token,
            challenge,
            validate,
            seccode,
            source=source,
        )
        return await self._client._post_payload(
            "/x/passport-login/web/sms/send",
            {},
            SMS_SEND,
            form=form,
            host="passport.bilibili.com",
        )

    async def login_with_sms(
        self, *, cid: int, tel: int, captcha_key: str, code: str
    ) -> None:
        response = await self._client._send_response(
            "POST",
            "/x/passport-login/web/login/sms",
            {},
            form=sms_login_form(cid, tel, captcha_key, code),
            host="passport.bilibili.com",
        )
        decode_payload(response.content, SMS_LOGIN)

    async def update_user_sign(self, *, user_sign: str) -> JsonValue:
        if not isinstance(user_sign, str) or len(user_sign.encode("utf-8")) > 70:
            user_sign_form(user_sign, "")
        csrf = self._client.csrf()
        return await self._client._post_payload(
            "/x/member/web/sign/update",
            {},
            OPTIONAL_JSON,
            form=user_sign_form(user_sign, csrf),
            optional=True,
        )
