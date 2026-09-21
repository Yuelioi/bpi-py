from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from types import TracebackType
from typing import Any, Literal, TypeVar

import httpx
from pydantic import TypeAdapter

from bpi._core.response import ResponseModel, decode_payload
from bpi.activity.client import ActivityClient
from bpi.article.client import ArticleClient
from bpi.audio.client import AudioClient
from bpi.bangumi.client import BangumiClient
from bpi.cheese.client import CheeseClient
from bpi.clientinfo.client import ClientInfoClient
from bpi.comment.client import CommentClient
from bpi.creativecenter.client import CreativeCenterClient
from bpi.danmaku.client import DanmakuClient
from bpi.dynamic.client import DynamicClient
from bpi.electric.client import ElectricClient
from bpi.errors import (
    AuthenticationError,
    ClientClosedError,
    HttpStatusError,
    InvalidParameterError,
    ResponseDecodeError,
    TransportError,
)
from bpi.fav.client import FavClient
from bpi.historytoview.client import HistoryToViewClient
from bpi.live.client import LiveClient
from bpi.login.client import LoginClient
from bpi.login.models import LoginWbiImg
from bpi.manga.client import MangaClient
from bpi.message.client import MessageClient
from bpi.misc.client import MiscClient
from bpi.note.client import NoteClient
from bpi.opus.client import OpusClient
from bpi.search.client import SearchClient
from bpi.session import Account, parse_cookie
from bpi.sign.wbi import key_from_url, mixin_key, sign_params
from bpi.user.client import UserClient
from bpi.video.client import VideoClient
from bpi.video_ranking.client import VideoRankingClient
from bpi.vip.client import VipClient
from bpi.wallet.client import WalletClient
from bpi.web_widget.client import WebWidgetClient

T = TypeVar("T")
ApiHost = Literal[
    "api.bilibili.com",
    "www.bilibili.com",
    "api.vc.bilibili.com",
    "api.live.bilibili.com",
    "api.biliapi.net",
    "account.bilibili.com",
    "comment.bilibili.com",
    "live-trace.bilibili.com",
    "manga.bilibili.com",
    "member.bilibili.com",
    "pay.bilibili.com",
    "passport.bilibili.com",
    "s.search.bilibili.com",
]
API_HOSTS: tuple[ApiHost, ...] = (
    "api.bilibili.com",
    "www.bilibili.com",
    "api.vc.bilibili.com",
    "api.live.bilibili.com",
    "api.biliapi.net",
    "account.bilibili.com",
    "comment.bilibili.com",
    "live-trace.bilibili.com",
    "manga.bilibili.com",
    "member.bilibili.com",
    "pay.bilibili.com",
    "passport.bilibili.com",
    "s.search.bilibili.com",
)
HEADERS = {
    "user-agent": "Mozilla/5.0",
    "referer": "https://www.bilibili.com/",
    "origin": "https://www.bilibili.com",
}


class _WbiData(ResponseModel):
    wbi_img: LoginWbiImg


WBI = TypeAdapter(_WbiData)


class AsyncBpiClient:
    """Asyncio SDK client. Use in one event loop; no automatic retries or account loading.

    A supplied HTTPX client is borrowed and owns its Cookie configuration. Do not combine
    it with SDK cookie/account/transport/proxy arguments. External HTTPX hooks and logging
    are controlled by its owner.
    """

    def __init__(
        self,
        *,
        cookie: str | None = None,
        account: Account | None = None,
        timeout: float = 15.0,
        proxy: str | None = None,
        trust_env: bool = True,
        http_client: httpx.AsyncClient | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if cookie is not None and account is not None:
            raise InvalidParameterError("Choose cookie or account")
        if http_client is not None and any(
            x is not None for x in (cookie, account, transport, proxy)
        ):
            raise InvalidParameterError(
                "Configure session and transport on the borrowed HTTP client"
            )
        pairs = parse_cookie(account.cookie_header() if account else cookie or "")
        self._owned = http_client is None
        self._http = (
            http_client
            if http_client is not None
            else httpx.AsyncClient(
                timeout=timeout, proxy=proxy, trust_env=trust_env, transport=transport
            )
        )
        for name, value in pairs.items():
            self._http.cookies.set(name, value, domain=".bilibili.com", path="/")
        self._closed = False
        self._clock = clock
        self._keys: tuple[str, str] | None = None
        self._bucket: int | None = None
        self._key_lock = asyncio.Lock()
        self.video = VideoClient(self)
        self.article = ArticleClient(self)
        self.comment = CommentClient(self)
        self.creativecenter = CreativeCenterClient(self)
        self.danmaku = DanmakuClient(self)
        self.dynamic = DynamicClient(self)
        self.electric = ElectricClient(self)
        self.login = LoginClient(self)
        self.bangumi = BangumiClient(self)
        self.audio = AudioClient(self)
        self.cheese = CheeseClient(self)
        self.user = UserClient(self)
        self.search = SearchClient(self)
        self.fav = FavClient(self)
        self.historytoview = HistoryToViewClient(self)
        self.live = LiveClient(self)
        self.manga = MangaClient(self)
        self.message = MessageClient(self)
        self.misc = MiscClient(self)
        self.note = NoteClient(self)
        self.video_ranking = VideoRankingClient(self)
        self.vip = VipClient(self)
        self.opus = OpusClient(self)
        self.wallet = WalletClient(self)
        self.clientinfo = ClientInfoClient(self)
        self.activity = ActivityClient(self)
        self.web_widget = WebWidgetClient(self)

    async def __aenter__(self) -> AsyncBpiClient:
        self._check_open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    def _check_open(self) -> None:
        if self._closed or self._http.is_closed:
            raise ClientClosedError("Client is closed")

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            if self._owned:
                await self._http.aclose()

    def csrf(self) -> str:
        """Get CSRF from the active Cookie jar without exposing it in diagnostics."""
        return self._csrf()

    def _csrf(self, *, host: ApiHost = "api.bilibili.com", optional: bool = False) -> str:
        self._check_open()
        if host not in API_HOSTS:
            raise InvalidParameterError("Unsupported API host")
        request = self._http.build_request("GET", f"https://{host}/")
        token = parse_cookie(request.headers.get("cookie", "")).get("bili_jct")
        if not token and not optional:
            raise AuthenticationError(-101)
        return token or ""

    async def _get(
        self,
        path: str,
        params: dict[str, str],
        *,
        host: ApiHost = "api.bilibili.com",
        referer: str | None = None,
    ) -> bytes:
        return await self._send("GET", path, params, host=host, referer=referer)

    async def _get_raw(
        self,
        path: str,
        params: dict[str, str],
        *,
        host: ApiHost = "api.bilibili.com",
        referer: str | None = None,
    ) -> bytes:
        self._check_open()
        if host not in API_HOSTS:
            raise InvalidParameterError("Unsupported API host")
        response: httpx.Response | None = None
        try:
            url = httpx.URL(f"https://{host}" + path).copy_merge_params(params)
            headers = HEADERS if referer is None else {**HEADERS, "referer": referer}
            request = self._http.build_request("GET", url, headers=headers)
            request.url = url
            response = await self._http.send(request, follow_redirects=False, stream=True)
            if not 200 <= response.status_code < 300:
                raise HttpStatusError(response.status_code)
            return b"".join([chunk async for chunk in response.aiter_raw()])
        except httpx.HTTPError:
            raise TransportError("HTTP transport failed") from None
        finally:
            if response is not None:
                await response.aclose()

    async def _send(
        self,
        method: str,
        path: str,
        params: dict[str, str],
        *,
        form: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
        multipart: bool = False,
        file_part: tuple[str, str, bytes, str] | None = None,
        host: ApiHost = "api.bilibili.com",
        referer: str | None = None,
    ) -> bytes:
        response = await self._send_response(
            method,
            path,
            params,
            form=form,
            json_body=json_body,
            multipart=multipart,
            file_part=file_part,
            host=host,
            referer=referer,
        )
        return response.content

    async def _send_response(
        self,
        method: str,
        path: str,
        params: dict[str, str],
        *,
        form: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
        multipart: bool = False,
        file_part: tuple[str, str, bytes, str] | None = None,
        host: ApiHost = "api.bilibili.com",
        referer: str | None = None,
    ) -> httpx.Response:
        self._check_open()
        if host not in API_HOSTS:
            raise InvalidParameterError("Unsupported API host")
        try:
            # Explicitly disable redirects even for a borrowed client.
            url = httpx.URL(f"https://{host}" + path).copy_merge_params(params)
            headers = HEADERS if referer is None else {**HEADERS, "referer": referer}
            if multipart:
                files: Any = {key: (None, value) for key, value in (form or {}).items()}
                if file_part is not None:
                    field, filename, body, content_type = file_part
                    files[field] = (filename, body, content_type)
                request = self._http.build_request(
                    method,
                    url,
                    headers=headers,
                    files=files,
                )
            elif json_body is not None:
                request = self._http.build_request(method, url, headers=headers, json=json_body)
            else:
                request = self._http.build_request(method, url, headers=headers, data=form)
            # Borrowed-client default query parameters must not invalidate the WBI signature.
            request.url = url
            response = await self._http.send(request, follow_redirects=False)
        except httpx.HTTPError:
            raise TransportError("HTTP transport failed") from None
        if not 200 <= response.status_code < 300:
            raise HttpStatusError(response.status_code)
        return response

    async def _get_payload(
        self,
        path: str,
        params: dict[str, str],
        adapter: TypeAdapter[T],
        *,
        host: ApiHost = "api.bilibili.com",
        optional: bool = False,
        referer: str | None = None,
    ) -> T:
        return decode_payload(
            await self._get(path, params, host=host, referer=referer),
            adapter,
            allow_missing=optional,
        )

    async def _post_payload(
        self,
        path: str,
        params: dict[str, str],
        adapter: TypeAdapter[T],
        *,
        form: dict[str, str] | None = None,
        multipart: bool = False,
        optional: bool = False,
        host: ApiHost = "api.bilibili.com",
        referer: str | None = None,
    ) -> T:
        body = await self._send(
            "POST",
            path,
            params,
            form=form,
            multipart=multipart,
            host=host,
            referer=referer,
        )
        return decode_payload(body, adapter, allow_missing=optional)

    async def _post_multipart_payload(
        self,
        path: str,
        params: dict[str, str],
        adapter: TypeAdapter[T],
        *,
        form: dict[str, str],
        file_part: tuple[str, str, bytes, str] | None = None,
        optional: bool = False,
        host: ApiHost = "api.bilibili.com",
        referer: str | None = None,
    ) -> T:
        body = await self._send(
            "POST",
            path,
            params,
            form=form,
            multipart=True,
            file_part=file_part,
            host=host,
            referer=referer,
        )
        return decode_payload(body, adapter, allow_missing=optional)

    async def _post_json_payload(
        self,
        path: str,
        params: dict[str, str],
        adapter: TypeAdapter[T],
        *,
        json_body: dict[str, object],
        optional: bool = False,
        host: ApiHost = "api.bilibili.com",
        referer: str | None = None,
    ) -> T:
        body = await self._send(
            "POST",
            path,
            params,
            json_body=json_body,
            host=host,
            referer=referer,
        )
        return decode_payload(body, adapter, allow_missing=optional)

    async def _sign(self, params: dict[str, str]) -> dict[str, str]:
        self._check_open()
        async with self._key_lock:
            bucket = int(self._clock()) // 3600
            if self._keys is None or bucket != self._bucket:
                body = await self._get("/x/web-interface/nav", {})
                data = decode_payload(body, WBI, allow_anonymous_wbi=True)
                try:
                    keys = (key_from_url(data.wbi_img.img_url), key_from_url(data.wbi_img.sub_url))
                    mixin_key(*keys)
                except (InvalidParameterError, ValueError):
                    raise ResponseDecodeError(body) from None
                self._keys, self._bucket = keys, bucket
            keys = self._keys
        return sign_params(params, *keys, int(self._clock()))
