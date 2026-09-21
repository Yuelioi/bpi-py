from __future__ import annotations

import asyncio
import hashlib
import json
import traceback
from pathlib import Path

import httpx
import pytest
from pydantic import TypeAdapter

from bpi import (
    Account,
    ApiError,
    AsyncBpiClient,
    AuthenticationError,
    BpiError,
    ClientClosedError,
    HttpStatusError,
    InvalidParameterError,
    MissingDataError,
    ResponseDecodeError,
    TransportError,
    UnsupportedResponseError,
)
from bpi._core.response import decode_payload
from bpi.login.models import LoginNav
from bpi.sign.wbi import mixin_key, sign_params
from bpi.video.models import DashStream, DurlInfo, PlayUrlResponseData, VideoView

FIXTURES = Path(__file__).parent / "fixtures"
IMG = "abcdefghijklmnopqrstuvwxyz123456"
SUB = "ABCDEFGHIJKLMNOPQRSTUVWXYZ654321"
NOW = 1_700_000_000
WBI_BODY = {
    "code": -101,
    "data": {
        "wbi_img": {
            "img_url": f"https://example.invalid/{IMG}.png",
            "sub_url": f"https://example.invalid/{SUB}.png",
        }
    },
}
VIEW_PATH = "video/info-read/view/responses/success.json"
PLAY_PATH = "video/playurl/play-url/responses/success.json"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("SDK tests must not access the network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def fixture(path: str) -> bytes:
    return (FIXTURES / path).read_bytes()


def cases():
    for path in sorted(FIXTURES.rglob("contract.json")):
        contract = json.loads(path.read_bytes())
        for case in contract["cases"]:
            yield pytest.param(path, contract, case, id=f"{contract['name']}:{case['name']}")


@pytest.mark.parametrize("path,contract,case", list(cases()))
async def test_contracts_through_public_methods(path, contract, case):
    calls = []
    expected = contract["request"]
    body = (path.parent / case["response"]["fixture"]).read_bytes()
    cookie = "SESSDATA=test-session; bili_jct=test-csrf" if case["profile"] != "anonymous" else None

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/nav") and contract["name"] == "video.play_url":
            return httpx.Response(200, json=WBI_BODY)
        assert str(request.url).split("?")[0] == expected["url"]
        assert request.method == expected["method"]
        assert all(name in request.headers for name in expected["required_headers"])
        assert ("SESSDATA=test-session" in request.headers.get("cookie", "")) == bool(cookie)
        query = dict(request.url.params)
        if contract["name"] == "video.play_url":
            assert query == sign_params(expected["query"], IMG, SUB, NOW)
        else:
            assert query == expected["query"]
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie=cookie, transport=httpx.MockTransport(handler), clock=lambda: NOW
    ) as client:

        async def invoke():
            match contract["name"]:
                case "login.nav":
                    return await client.login.nav()
                case "video.view":
                    return await client.video.view(bvid="BV1xx411c7mD")
                case "video.pagelist":
                    return await client.video.page_list(bvid="BV1xx411c7mD")
                case "video.play_url":
                    return await client.video.play_url(
                        bvid="BV1xx411c7mD",
                        cid=62131,
                        quality=32,
                        format_flags=16,
                        format_version=0,
                    )

        if case["response"]["api_code"] != 0:
            with pytest.raises(AuthenticationError) as error:
                await invoke()
            assert error.value.requires_login()
        else:
            result = await invoke()
            if contract["name"] == "video.view":
                assert result.title == json.loads(body)["data"]["title"]
                assert result.owner.name
            elif contract["name"] == "video.pagelist":
                assert result[0].cid == 62131
            elif contract["name"] == "video.play_url":
                assert result.dash.video[0].base_url
            else:
                assert result.is_login
    assert len(calls) == (2 if contract["name"] == "video.play_url" else 1)


def test_fixture_provenance():
    data = json.loads(fixture("provenance.json"))
    assert data["source_commit"] == "4b8d49126d34c32b0067d93d87976c3a7f97b4c5"
    for path, digest in data["sha256"].items():
        assert hashlib.sha256(fixture(path)).hexdigest() == digest


def test_wbi_rust_golden_vector_and_reserved_characters():
    assert mixin_key(IMG, SUB) == "OPscVixApSk66dND2LfRBjKt43oHmGJn"
    params = {"foo": "value!'()*", "bar": "space value"}
    assert sign_params(params, IMG, SUB, NOW) == {
        "bar": "space value",
        "foo": "value",
        "w_rid": "e0bbf3c23838f46f9b7b2785d19dd01e",
        "wts": "1700000000",
    }
    assert params["foo"] == "value!'()*"


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"aid": 1, "bvid": "BV1xx411c7mD"}, {"aid": True}, {"aid": -1}, {"bvid": "invalid"}],
)
async def test_invalid_identifiers_make_no_request(kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.video.view(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cid": True},
        {"cid": 0},
        {"cid": 1, "quality": True},
        {"cid": 1, "fourk": 1},
        {"cid": 1, "platform": ""},
    ],
)
async def test_invalid_play_parameters_make_no_request(kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.video.play_url(aid=2, **kwargs)


async def test_aid_and_avid_and_boolean_encoding():
    queries = []

    def handler(request):
        if request.url.path.endswith("/nav"):
            return httpx.Response(200, json=WBI_BODY)
        queries.append(dict(request.url.params))
        return httpx.Response(
            200, content=fixture(PLAY_PATH if "playurl" in request.url.path else VIEW_PATH)
        )

    async with AsyncBpiClient(transport=httpx.MockTransport(handler), clock=lambda: NOW) as client:
        await client.video.view(aid=2)
        await client.video.play_url(
            aid=2, cid=62131, fourk=False, high_quality=True, try_look=False
        )
    assert queries[0] == {"aid": "2"}
    assert queries[1]["avid"] == "2" and "aid" not in queries[1]
    assert {k: queries[1][k] for k in ("fourk", "high_quality", "try_look")} == {
        "fourk": "0",
        "high_quality": "1",
        "try_look": "0",
    }


async def test_api_error_precedes_invalid_payload_and_no_retry():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"code": -352, "message": "private-marker", "data": []})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ApiError) as error:
            await client.video.view(aid=2)
    assert error.value.is_risk_control() and error.value.message == "private-marker"
    assert "private-marker" not in repr(error.value)
    assert calls == 1


async def test_decode_failure_retains_exact_body_without_replay_or_traceback_leak():
    data = json.loads(fixture(VIEW_PATH))
    data["data"]["aid"] = "private-marker"
    body = json.dumps(data).encode()
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ResponseDecodeError) as error:
            await client.video.view(aid=2)
    assert error.value.response_body == body
    assert json.loads(error.value.response_body)["data"]["aid"] == "private-marker"
    assert "private-marker" not in "".join(traceback.format_exception(error.value))
    assert calls == 1


@pytest.mark.parametrize(
    "body,error",
    [
        (b"not json", ResponseDecodeError),
        (b"[]", ResponseDecodeError),
        (b'{"code":true}', ResponseDecodeError),
        (b'{"code":0}', MissingDataError),
        (b'{"code":0,"data":null}', MissingDataError),
    ],
)
def test_invalid_envelopes(body, error):
    with pytest.raises(error):
        decode_payload(body, TypeAdapter(VideoView))


def test_error_semantics_match_rust_contract():
    assert ApiError(-101).semantic_error() == "requires_login"
    assert ApiError(-106).semantic_error() == "requires_vip"
    assert ApiError(-403).semantic_error() == "permission_denied"
    assert ApiError(-352).semantic_error() == "risk_control"
    assert HttpStatusError(401).semantic_error() == "requires_login"
    assert HttpStatusError(403).semantic_error() == "permission_denied"
    assert HttpStatusError(412).semantic_error() == "risk_control"
    assert issubclass(UnsupportedResponseError, BpiError)


def test_envelope_aliases_and_unknown_fields():
    payload = json.loads(fixture(VIEW_PATH))["data"]
    payload["future_field"] = {"unknown": True}
    view = decode_payload(
        json.dumps({"errno": 0, "msg": "OK", "result": payload}).encode(), TypeAdapter(VideoView)
    )
    assert view.aid == 2 and "future_field" not in view.model_dump()


def test_playback_nullable_backups_and_signed_sentinels():
    stream = {
        "id": 1,
        "baseUrl": "url",
        "backupUrl": None,
        "bandwidth": 1,
        "mimeType": "video/mp4",
        "codecs": "avc",
    }
    assert DashStream.model_validate(stream).backup_url == []
    assert DurlInfo(order=1, length=1, size=1, ahead="", vhead="", url="url").backup_url == []
    payload = json.loads(fixture(PLAY_PATH))["data"]
    payload["last_play_time"] = -1
    payload["last_play_cid"] = -1
    assert PlayUrlResponseData.model_validate(payload).last_play_time == -1


async def test_parallel_wbi_fetch_once_and_refresh_next_hour():
    now = [NOW]
    fetches = 0

    async def handler(request):
        nonlocal fetches
        if request.url.path.endswith("/nav"):
            fetches += 1
            await asyncio.sleep(0)
            return httpx.Response(200, json=WBI_BODY)
        return httpx.Response(200, content=fixture(PLAY_PATH))

    async with AsyncBpiClient(
        transport=httpx.MockTransport(handler), clock=lambda: now[0]
    ) as client:
        await asyncio.gather(*(client.video.play_url(aid=2, cid=62131) for _ in range(8)))
        assert fetches == 1
        now[0] += 3600
        await client.video.play_url(aid=2, cid=62131)
        assert fetches == 2


async def test_wbi_refresh_failure_is_not_cached_and_other_errors_are_not_accepted():
    fetches = 0

    def handler(request):
        nonlocal fetches
        if request.url.path.endswith("/nav"):
            fetches += 1
            return httpx.Response(
                200, json={**WBI_BODY, "code": -352} if fetches == 1 else WBI_BODY
            )
        return httpx.Response(200, content=fixture(PLAY_PATH))

    async with AsyncBpiClient(transport=httpx.MockTransport(handler), clock=lambda: NOW) as client:
        with pytest.raises(ApiError):
            await client.video.play_url(aid=2, cid=62131)
        await client.video.play_url(aid=2, cid=62131)
    assert fetches == 2


async def test_cancelled_refresh_releases_lock():
    entered = asyncio.Event()
    fetches = 0

    async def handler(request):
        nonlocal fetches
        if request.url.path.endswith("/nav"):
            fetches += 1
            if fetches == 1:
                entered.set()
                await asyncio.Event().wait()
            return httpx.Response(200, json=WBI_BODY)
        return httpx.Response(200, content=fixture(PLAY_PATH))

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        task = asyncio.create_task(client.video.play_url(aid=2, cid=62131))
        await asyncio.wait_for(entered.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.wait_for(client.video.play_url(aid=2, cid=62131), 1)


async def test_session_isolation_owned_close_and_borrowed_close():
    cookies = []

    def handler(request):
        cookies.append(request.headers.get("cookie", ""))
        return httpx.Response(200, content=fixture(VIEW_PATH))

    one = AsyncBpiClient(
        account=Account("session-a", "csrf-a"), transport=httpx.MockTransport(handler)
    )
    two = AsyncBpiClient(transport=httpx.MockTransport(handler))
    async with one, two:
        assert one.csrf() == "csrf-a"
        with pytest.raises(AuthenticationError):
            two.csrf()
        await one.video.view(aid=2)
        await two.video.view(aid=2)
    assert "session-a" in cookies[0] and cookies[1] == ""
    assert one._http.is_closed
    with pytest.raises(ClientClosedError):
        await one.video.view(aid=2)
    external = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncBpiClient(http_client=external) as borrowed:
        await borrowed.video.view(aid=2)
    assert not external.is_closed
    await external.aclose()
    assert "session-a" not in repr(Account("session-a", "csrf-a"))


async def test_redirect_is_not_followed_and_transport_error_is_safe():
    count = 0

    def handler(request):
        nonlocal count
        count += 1
        return httpx.Response(302, headers={"location": "https://example.invalid/leak"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), follow_redirects=True
    ) as external:
        async with AsyncBpiClient(http_client=external) as client:
            with pytest.raises(HttpStatusError) as error:
                await client.video.view(aid=2)
            assert error.value.status_code == 302
    assert count == 1

    def failing(request):
        raise httpx.ConnectError("secret-cookie", request=request)

    async with AsyncBpiClient(transport=httpx.MockTransport(failing)) as client:
        with pytest.raises(TransportError) as error:
            await client.video.view(aid=2)
    assert "secret-cookie" not in "".join(traceback.format_exception(error.value))


def test_anonymous_nav_normalization():
    model = LoginNav.model_validate(
        {
            "isLogin": False,
            "mid": 0,
            "uname": "",
            "face": "",
            "wbi_img": WBI_BODY["data"]["wbi_img"],
        }
    )
    assert model.mid is None and model.uname is None and model.face is None


@pytest.mark.parametrize("cookie", ["SESSDATA=a\r\nX-Header: leak", "invalid-pair"])
def test_invalid_cookie(cookie):
    with pytest.raises(InvalidParameterError):
        AsyncBpiClient(cookie=cookie)


async def test_borrowed_default_query_does_not_change_signed_request():
    observed = []

    def handler(request):
        observed.append(dict(request.url.params))
        if request.url.path.endswith("/nav"):
            return httpx.Response(200, json=WBI_BODY)
        return httpx.Response(200, content=fixture(PLAY_PATH))

    async with httpx.AsyncClient(
        params={"injected": "default"}, transport=httpx.MockTransport(handler)
    ) as external:
        async with AsyncBpiClient(http_client=external, clock=lambda: NOW) as client:
            await client.video.play_url(aid=2, cid=62131)
    assert observed[0] == {}
    assert observed[1] == sign_params(
        {"avid": "2", "cid": "62131", "platform": "pc"}, IMG, SUB, NOW
    )


async def test_borrowed_session_options_rejected_without_closing_owner():
    async with httpx.AsyncClient() as external:
        with pytest.raises(InvalidParameterError):
            AsyncBpiClient(http_client=external, cookie="SESSDATA=test")
        assert not external.is_closed


async def test_invalid_wbi_keys_keep_body_and_can_recover_on_next_call():
    body = json.dumps(
        {
            "code": 0,
            "data": {
                "wbi_img": {
                    "img_url": "invalid",
                    "sub_url": "invalid",
                }
            },
        }
    ).encode()
    count = 0

    def handler(request):
        nonlocal count
        if request.url.path.endswith("/nav"):
            count += 1
            return (
                httpx.Response(200, content=body)
                if count == 1
                else httpx.Response(200, json=WBI_BODY)
            )
        return httpx.Response(200, content=fixture(PLAY_PATH))

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ResponseDecodeError) as error:
            await client.video.play_url(aid=2, cid=62131)
        assert error.value.response_body == body
        await client.video.play_url(aid=2, cid=62131)
    assert count == 2
