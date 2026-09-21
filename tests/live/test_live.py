from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest

from bpi import ApiError, AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.live import LiveClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
LIVE_FIXTURES = FIXTURES / "live"
SIGNED_READS = {"live.danmu_info", "live.lottery_info"}
WBI_BODY = {
    "code": -101,
    "data": {
        "wbi_img": {
            "img_url": "https://example.invalid/abcdefghijklmnopqrstuvwxyz123456.png",
            "sub_url": "https://example.invalid/ABCDEFGHIJKLMNOPQRSTUVWXYZ654321.png",
        }
    },
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Live tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


READS = [
    (
        "account-private-read/follow-up-list",
        "follow_up_list",
        {"page": 1, "page_size": 2, "ignore_record": 1, "hit_ab": True},
    ),
    ("account-private-read/follow-up-web-list", "follow_up_web_list", {"hit_ab": False}),
    ("account-private-read/my-medals", "my_medals", {}),
    ("account-private-read/replay-list", "replay_list", {"page": 1, "page_size": 2}),
    ("gift-read/blind-gift-info", "blind_gift_info", {"gift_id": 32251}),
    ("gift-read/gift-types", "gift_types", {}),
    ("gift-read/room-gift-list", "room_gift_list", {"room_id": 23174842}),
    ("guard-read/guard-list", "guard_list", {"room_id": 23174842, "ruid": 504140200}),
    (
        "moderation-private-read/banned-users",
        "banned_users",
        {"room_id": 3818081, "anchor_id": 1000001},
    ),
    ("moderation-private-read/shield-keywords", "shield_keywords", {"room_id": 3818081}),
    ("moderation-private-read/silent-users", "silent_users", {"room_id": 3818081}),
    ("public-core/area-list", "area_list", {}),
    ("public-core/recommend", "recommend", {}),
    ("public-core/room-info", "room_info", {"room_id": 23174842}),
    ("public-core/stream", "stream", {"cid": 14073662, "platform": "web", "qn": 10000}),
    ("public-core/version", "version", {}),
    ("room-interaction-read/danmu-info", "danmu_info", {"room_id": 21733448, "info_type": 0}),
    ("room-interaction-read/emoticons", "emoticons", {"room_id": 14047, "platform": "pc"}),
    ("room-interaction-read/lottery-info", "lottery_info", {"room_id": 23174842}),
    ("telemetry-read/heartbeat", "web_heart_beat", {"room_id": 23174842}),
]


def _cookie_for_case(case: dict[str, object]) -> str | None:
    profile = case.get("profile")
    if profile in {"normal", "vip", "authenticated"}:
        return "SESSDATA=fake; bili_jct=token"
    return None


def _replace_csrf(values: dict[str, str], authenticated: bool) -> dict[str, str]:
    token = "token" if authenticated else ""
    return {key: (token if value == "${csrf}" else value) for key, value in values.items()}


def _form_values(request: httpx.Request) -> dict[str, str]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        text = request.content.decode("utf-8")
        return dict(re.findall(r'name="([^"]+)"\r\n\r\n(.*?)\r\n', text, re.S))
    return dict(parse_qsl(request.content.decode(), keep_blank_values=True))


@pytest.mark.parametrize("directory,method,kwargs", READS, ids=[case[0] for case in READS])
async def test_promoted_read_contracts_all_profiles(directory, method, kwargs):
    contract = json.loads((LIVE_FIXTURES / directory / "contract.json").read_bytes())
    expected = contract["request"]

    for case in contract["cases"]:
        cookie = _cookie_for_case(case)
        authenticated = cookie is not None
        body = (LIVE_FIXTURES / directory / case["response"]["fixture"]).read_bytes()
        target_calls: list[httpx.Request] = []

        def handler(
            request: httpx.Request,
            *,
            target_calls: list[httpx.Request] = target_calls,
            authenticated: bool = authenticated,
            body: bytes = body,
        ) -> httpx.Response:
            if request.url.path == "/x/web-interface/nav":
                return httpx.Response(200, json=WBI_BODY)

            target_calls.append(request)
            assert request.method == expected["method"]
            assert str(request.url).split("?")[0] == expected["url"]
            actual_query = dict(request.url.params)
            if contract["name"] in SIGNED_READS:
                assert actual_query.pop("wts", "").isdigit()
                assert len(actual_query.pop("w_rid", "")) == 32
            assert actual_query == _replace_csrf(expected["query"], authenticated)
            if expected.get("form") is not None:
                assert _form_values(request) == _replace_csrf(expected["form"], authenticated)
            if expected.get("headers", {}).get("referer"):
                assert request.headers["referer"] == expected["headers"]["referer"]
            return httpx.Response(200, content=body)

        async with AsyncBpiClient(
            cookie=cookie,
            transport=httpx.MockTransport(handler),
            clock=lambda: 1700000000.0,
        ) as client:
            call = getattr(client.live, method)
            code = case["response"].get("api_code")
            if code == 0:
                assert await call(**kwargs) is not None
            else:
                with pytest.raises(ApiError) as error:
                    await call(**kwargs)
                assert error.value.code == code

        assert len(target_calls) == 1


START_DATA = {
    "change": 1,
    "status": "LIVE",
    "rtmp": {"addr": "rtmp://example.invalid/live", "code": "key"},
    "live_key": "live-key",
    "sub_session_key": "session",
    "need_face_auth": False,
    "room_type": {},
    "protocols": {},
    "notice": {},
    "qr": {},
    "service_source": "web",
    "rtmp_backup": {},
    "up_stream_extra": {},
}

WRITES = [
    (
        "live_send_danmu",
        {"room_id": 1, "message": "hello", "color": 255, "font_size": 25},
        "/msg/send",
        True,
        {
            "csrf": "token",
            "roomid": "1",
            "msg": "hello",
            "rnd": "1700000000",
            "bubble": "0",
            "mode": "1",
            "statistics": '{"appId":100,"platform":5}',
            "csrf_token": "token",
            "color": "255",
            "fontsize": "25",
        },
        {},
        {"mode_info": None, "dm_v2": None},
        None,
    ),
    (
        "live_create_room",
        {},
        "/xlive/app-blink/v1/preLive/CreateRoom",
        True,
        {"platform": "web", "visit_id": "", "csrf": "token", "csrf_token": "token"},
        {},
        {"roomID": "1"},
        None,
    ),
    (
        "live_update_room_info",
        {"room_id": 1, "title": "title", "area_id": 2, "add_tag": "a", "del_tag": "b"},
        "/room/v1/Room/update",
        True,
        {
            "room_id": "1",
            "csrf": "token",
            "csrf_token": "token",
            "title": "title",
            "area_id": "2",
            "add_tag": "a",
            "del_tag": "b",
        },
        {},
        {"sub_session_key": "s", "audit_info": None},
        None,
    ),
    (
        "live_fetch_web_up_stream_addr",
        {},
        "/xlive/app-blink/v1/live/FetchWebUpStreamAddr",
        False,
        {"platform": "pc", "backup_stream": "0", "csrf": "token", "csrf_token": "token"},
        {},
        {
            "addr": {"addr": "rtmp://example.invalid/live", "code": "key"},
            "line": {},
            "srt_addr": {},
        },
        None,
    ),
    (
        "live_web_center_start",
        {"room_id": 1, "area_v2": 2},
        "/xlive/app-blink/v1/streaming/WebLiveCenterStartLive",
        False,
        {},
        {
            "room_id": "1",
            "platform": "pc",
            "area_v2": "2",
            "backup_stream": "0",
            "csrf": "token",
            "csrf_token": "token",
        },
        START_DATA,
        None,
    ),
    (
        "live_stop",
        {"room_id": 1, "platform": "pc_link"},
        "/room/v1/Room/stopLive",
        True,
        {"platform": "pc_link", "room_id": "1", "csrf": "token", "csrf_token": "token"},
        {},
        {"change": 1, "status": "PREPARING"},
        None,
    ),
    (
        "live_update_pre_live_info",
        {"title": "title", "cover": "https://example.invalid/c.jpg"},
        "/xlive/app-blink/v1/preLive/UpdatePreLiveInfo",
        True,
        {
            "platform": "web",
            "mobi_app": "web",
            "build": "1",
            "csrf": "token",
            "csrf_token": "token",
            "title": "title",
            "cover": "https://example.invalid/c.jpg",
        },
        {},
        {"audit_info": None},
        None,
    ),
    (
        "live_update_room_news",
        {"room_id": 1, "uid": 2, "content": "news"},
        "/xlive/app-blink/v1/index/updateRoomNews",
        True,
        {"room_id": "1", "uid": "2", "content": "news", "csrf": "token", "csrf_token": "token"},
        {},
        {},
        None,
    ),
    (
        "live_add_silent_user",
        {"room_id": 1, "tuid": 2, "hour": 0, "msg": "reason"},
        "/xlive/web-ucenter/v1/banned/AddSilentUser",
        False,
        {
            "room_id": "1",
            "tuid": "2",
            "msg": "reason",
            "mobile_app": "web",
            "type": "2",
            "hour": "0",
            "csrf_token": "token",
            "csrf": "token",
        },
        {},
        None,
        None,
    ),
    (
        "live_del_block_user",
        {"room_id": 1, "tuid": 2},
        "/xlive/web-ucenter/v1/banned/DelSilentUser",
        False,
        {"room_id": "1", "tuid": "2", "csrf_token": "token", "csrf": "token"},
        {},
        None,
        None,
    ),
    (
        "live_add_banned_user",
        {"room_id": 1, "anchor_id": 3, "tuid": 2},
        "/xlive/app-ucenter/v2/xbanned/banned/AddBlack",
        False,
        {
            "tuid": "2",
            "anchor_id": "3",
            "spmid": "444.8.0.0",
            "csrf_token": "token",
            "csrf": "token",
            "visit_id": "",
        },
        {},
        None,
        "https://live.bilibili.com/1",
    ),
    (
        "live_del_banned_user",
        {"room_id": 1, "anchor_id": 3, "tuid": 2},
        "/xlive/app-ucenter/v2/xbanned/banned/DelBlack",
        False,
        {
            "tuid": "2",
            "anchor_id": "3",
            "spmid": "444.8.0.0",
            "csrf_token": "token",
            "csrf": "token",
            "visit_id": "",
            "mobi_app": "android",
            "platform": "android",
        },
        {},
        None,
        "https://live.bilibili.com/1",
    ),
    (
        "live_add_shield_keyword",
        {"room_id": 1, "keyword": "spam"},
        "/xlive/app-ucenter/v1/banned/AddShieldKeyword",
        False,
        {
            "keyword": "spam",
            "room_id": "1",
            "spmid": "444.8.0.0",
            "csrf_token": "token",
            "csrf": "token",
            "visit_id": "",
            "mobi_app": "android",
            "platform": "android",
        },
        {},
        None,
        None,
    ),
    (
        "live_del_shield_keyword",
        {"room_id": 1, "keyword": "spam"},
        "/xlive/app-ucenter/v1/banned/DelShieldKeyword",
        False,
        {
            "keyword": "spam",
            "room_id": "1",
            "spmid": "444.8.0.0",
            "csrf_token": "token",
            "csrf": "token",
            "visit_id": "",
            "mobi_app": "android",
            "platform": "android",
        },
        {},
        None,
        None,
    ),
]


@pytest.mark.parametrize("case", WRITES, ids=[case[0] for case in WRITES])
@pytest.mark.parametrize("response_kind", ["success", "error"])
async def test_write_protocol_is_source_derived(case, response_kind):
    name, kwargs, path, multipart, expected_form, expected_query, data, referer = case
    target_calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/x/web-interface/nav":
            return httpx.Response(200, json=WBI_BODY)

        target_calls.append(request)
        assert request.method == "POST"
        assert request.url.host == "api.live.bilibili.com"
        assert request.url.path == path
        actual_query = dict(request.url.params)
        if name == "live_web_center_start":
            assert actual_query.pop("wts", "").isdigit()
            assert len(actual_query.pop("w_rid", "")) == 32
        assert actual_query == expected_query
        if multipart or expected_form:
            assert _form_values(request) == expected_form
        else:
            assert request.content == b""
        if referer is not None:
            assert request.headers["referer"] == referer
        if response_kind == "error":
            return httpx.Response(200, json={"code": -403, "message": "denied"})
        payload = {"code": 0, "message": "OK"}
        if data is not None:
            payload["data"] = data
        return httpx.Response(200, json=payload)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=token",
        transport=httpx.MockTransport(handler),
        clock=lambda: 1700000000.0,
    ) as client:
        method = getattr(client.live, name)
        if response_kind == "error":
            with pytest.raises(ApiError) as error:
                await method(**kwargs)
            assert error.value.code == -403
        else:
            await method(**kwargs)

    assert len(target_calls) == 1


@pytest.mark.parametrize("case", WRITES, ids=[case[0] for case in WRITES])
async def test_writes_require_csrf_before_target_request(case):
    name, kwargs = case[0], case[1]

    async with AsyncBpiClient() as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.live, name)(**kwargs)


@pytest.mark.parametrize(
    "name,kwargs",
    [
        ("room_info", {"room_id": 0}),
        ("stream", {"cid": 0}),
        ("stream", {"cid": 1, "platform": " "}),
        ("room_gift_list", {"room_id": 1, "area_id": 0}),
        ("blind_gift_info", {"gift_id": 0}),
        ("danmu_info", {"room_id": 1, "info_type": 256}),
        ("emoticons", {"room_id": 1, "platform": " "}),
        ("my_medals", {"page": 0}),
        ("follow_up_list", {"hit_ab": 1}),
        ("follow_up_list", {"ignore_record": 2}),
        ("guard_list", {"room_id": 1, "ruid": 2, "typ": 0}),
        ("silent_users", {"room_id": 0}),
        ("web_heart_beat", {"room_id": 1, "next_interval": 0}),
        ("live_send_danmu", {"room_id": 1, "message": " "}),
        ("live_stop", {"room_id": 1, "platform": " "}),
        ("live_add_silent_user", {"room_id": 1, "tuid": 2, "hour": -2}),
        ("live_add_shield_keyword", {"room_id": 1, "keyword": " "}),
    ],
)
async def test_invalid_arguments_fail_before_network(name, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.live, name)(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("live/")]
    assert len(paths) == 57
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_live_module_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "live"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.live.") and api["status"] == "implemented"
    }
    assert len(expected) == 34
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(LiveClient, name, None)) for name in expected)
