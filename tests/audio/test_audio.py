"""Audio-specific behavior and source-derived writes, entirely offline.

Read recordings live in tests/generated_reads/fixtures/audio. Write request
expectations follow Rust action.rs, params.rs and rank.rs; write responses and
edge-case bodies here are synthetic and do not claim live endpoint success.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest
from pydantic import ValidationError

from bpi import ApiError, AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.audio import AudioCollection, AudioRankPeriodData, PromptData
from bpi.audio.client import AudioClient
from bpi.errors import ClientClosedError, HttpStatusError, MissingDataError, ResponseDecodeError

ROOT = Path(__file__).resolve().parents[2]
# method, arguments, host, path, form, successful synthetic payload
WRITES = [
    (
        "favorite",
        {"rid": 1, "add_media_ids": [" 2 ", "3"], "del_media_ids": ["4"]},
        "api.bilibili.com",
        "/medialist/gateway/coll/resource/deal",
        {"rid": "1", "type": "12", "add_media_ids": "2,3", "del_media_ids": "4", "csrf": "token"},
        {"prompt": False},
    ),
    (
        "collect",
        {"sid": 1, "cids": 2},
        "www.bilibili.com",
        "/audio/music-service-c/web/collections/songs-coll",
        {"sid": "1", "cids": "2", "csrf": "token"},
        False,
    ),
    (
        "coin",
        {"sid": 1, "multiply": 2},
        "www.bilibili.com",
        "/audio/music-service-c/web/coin/add",
        {"sid": "1", "multiply": "2", "csrf": "token"},
        "",
    ),
    (
        "subscribe_rank",
        {"state": 2, "list_id": 76},
        "api.bilibili.com",
        "/x/copyright-music-publicity/toplist/subscribe/update",
        {"state": "2", "list_id": "76", "csrf": "token"},
        {"updated": True},
    ),
]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Audio tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize("case", WRITES, ids=[row[0] for row in WRITES])
@pytest.mark.parametrize("response_kind", ["success", "missing", "null", "error", "malformed"])
async def test_write_contracts(case, response_kind):
    name, kwargs, host, path, form, payload = case
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "POST"
        assert str(request.url) == f"https://{host}{path}"
        assert request.headers["content-type"] == "application/x-www-form-urlencoded"
        assert dict(parse_qsl(request.content.decode(), keep_blank_values=True)) == form
        assert "bili_jct=token" in request.headers["cookie"]
        assert all(h in request.headers for h in ("origin", "referer", "user-agent"))
        if response_kind == "malformed":
            return httpx.Response(200, content=b"not-json-sensitive-marker")
        body = {"code": 0, "data": payload}
        if response_kind == "missing":
            body = {"code": 0}
        elif response_kind == "null":
            body["data"] = None
        elif response_kind == "error":
            body = {"code": 4511003, "msg": "login needed", "data": "invalid"}
        return httpx.Response(200, json=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=token", transport=httpx.MockTransport(handler)
    ) as client:
        method = getattr(client.audio, name)
        if response_kind == "error":
            with pytest.raises(ApiError) as error:
                await method(**kwargs)
            assert error.value.code == 4511003
            assert isinstance(error.value, AuthenticationError)
            assert error.value.requires_login()
        elif response_kind == "malformed":
            with pytest.raises(ResponseDecodeError) as error:
                await method(**kwargs)
            assert error.value.response_body == b"not-json-sensitive-marker"
            assert "sensitive-marker" not in str(error.value)
        elif response_kind in ("missing", "null") and name != "subscribe_rank":
            with pytest.raises(MissingDataError):
                await method(**kwargs)
        else:
            value = await method(**kwargs)
            if response_kind in ("missing", "null"):
                assert value is None
            elif name == "favorite":
                assert isinstance(value, PromptData) and value.prompt is False
            else:
                assert type(value) is type(payload) and value == payload
    assert len(calls) == 1


@pytest.mark.parametrize("case", WRITES, ids=[row[0] for row in WRITES])
async def test_write_without_csrf_fails_before_network(case):
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.audio, case[0])(**case[1])


@pytest.mark.parametrize(
    "name,kwargs",
    [
        ("info", {"sid": 0}),
        ("tags", {"sid": True}),
        ("members", {"sid": "1"}),
        ("lyric", {"sid": -1}),
        ("status_number", {"sid": 0}),
        ("collection_status", {"sid": False}),
        ("coin_count", {"sid": 1.5}),
        ("collection_info", {"sid": 0}),
        ("stream_url_web", {"sid": 1, "quality": 4}),
        ("stream_url_web", {"sid": 1, "quality": True}),
        ("stream_url_web", {"sid": 1, "privilege": 0}),
        ("stream_url", {"song_id": 1, "quality": -1}),
        ("stream_url", {"song_id": 1, "quality": 2, "mid": 0}),
        ("stream_url", {"song_id": 1, "quality": 2, "platform": " \t"}),
        ("collections_list", {"page": 0, "page_size": 2}),
        ("hot_menu", {"page": 1, "page_size": 0}),
        ("rank_menu", {"page": True, "page_size": 2}),
        ("rank_period", {"list_type": 0}),
        ("rank_detail", {"list_id": 0}),
        ("rank_music_list", {"list_id": True}),
        ("favorite", {"rid": 1}),
        ("favorite", {"rid": 1, "add_media_ids": "123"}),
        ("favorite", {"rid": 1, "del_media_ids": [" "]}),
        ("collect", {"sid": 1, "cids": [2, 3]}),
        ("coin", {"sid": 1, "multiply": 3}),
        ("coin", {"sid": 1, "multiply": True}),
        ("subscribe_rank", {"state": 0}),
        ("subscribe_rank", {"state": True}),
        ("subscribe_rank", {"state": 1, "list_id": 0}),
    ],
)
async def test_invalid_arguments_never_reach_network(name, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.audio, name)(**kwargs)


@pytest.mark.parametrize(
    "name,kwargs,host,path,query",
    [
        (
            "stream_url_web",
            {"sid": 1},
            "www.bilibili.com",
            "/audio/music-service-c/web/url",
            {"sid": "1", "quality": "2", "privilege": "2"},
        ),
        (
            "stream_url_web",
            {"sid": 1, "quality": 0, "privilege": 4},
            "www.bilibili.com",
            "/audio/music-service-c/web/url",
            {"sid": "1", "quality": "0", "privilege": "4"},
        ),
        (
            "stream_url",
            {"song_id": 1, "quality": 3},
            "api.bilibili.com",
            "/audio/music-service-c/url",
            {"songid": "1", "quality": "3", "privilege": "2", "mid": "2", "platform": "android"},
        ),
        (
            "stream_url",
            {"song_id": 1, "quality": 1, "privilege": 4, "mid": 5, "platform": " ios "},
            "api.bilibili.com",
            "/audio/music-service-c/url",
            {"songid": "1", "quality": "1", "privilege": "4", "mid": "5", "platform": "ios"},
        ),
        (
            "collections_list",
            {"page": 2, "page_size": 9},
            "www.bilibili.com",
            "/audio/music-service-c/web/collections/list",
            {"pn": "2", "ps": "9"},
        ),
        (
            "rank_period",
            {"list_type": 9},
            "api.bilibili.com",
            "/x/copyright-music-publicity/toplist/all_period",
            {"list_type": "9", "csrf": ""},
        ),
    ],
)
async def test_read_query_defaults_and_variants(name, kwargs, host, path, query):
    def handler(request):
        assert request.method == "GET"
        assert request.url.host == host and request.url.path == path
        assert dict(request.url.params) == query
        return httpx.Response(200, json={"code": -400})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ApiError):
            await getattr(client.audio, name)(**kwargs)


@pytest.mark.parametrize(
    "name,kwargs,invalid",
    [
        ("collection_status", {"sid": 1}, "false"),
        ("collection_status", {"sid": 1}, 0),
        ("coin_count", {"sid": 1}, "1"),
        ("coin_count", {"sid": 1}, True),
        ("lyric", {"sid": 1}, False),
        ("collect", {"sid": 1, "cids": 2}, 1),
        ("coin", {"sid": 1, "multiply": 1}, False),
        ("favorite", {"rid": 1, "del_media_ids": ["2"]}, {"prompt": 0}),
    ],
)
async def test_scalar_type_drift_is_not_coerced(name, kwargs, invalid):
    body = json.dumps({"code": 0, "data": invalid}).encode()
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="bili_jct=token", transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(ResponseDecodeError) as error:
            await getattr(client.audio, name)(**kwargs)
        assert error.value.response_body == body
    assert len(calls) == 1


COLLECTION = {
    "id": 1,
    "uid": 2,
    "uname": "owner",
    "title": "folder",
    "type": 1,
    "published": 1,
    "cover": "",
    "ctime": 1,
    "song": 1,
    "desc": "",
    "sids": [3],
    "menuId": 4,
    "statistic": {"sid": 1, "play": 0, "collect": 0, "share": 0},
}


@pytest.mark.parametrize(
    "body", [{"code": 0}, {"code": 0, "data": None}, {"code": 0, "result": COLLECTION}]
)
async def test_optional_collection_and_aliases(body):
    async with AsyncBpiClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    ) as client:
        value = await client.audio.collection_info(sid=1)
        if "result" not in body:
            assert value is None
        else:
            assert isinstance(value, AudioCollection)
            assert value.menu_id == 4 and value.statistic.comment is None
            assert value.model_dump(by_alias=True)["menuId"] == 4


def test_rank_period_map_and_source_aliases():
    raw = {"list": {"2026": [{"ID": 76, "priod": 3, "publish_time": 1}]}}
    value = AudioRankPeriodData.model_validate(raw)
    assert value.list["2026"][0].id == 76
    assert value.list["2026"][0].priod == 3
    assert value.model_dump(by_alias=True) == raw
    with pytest.raises(ValidationError):
        AudioRankPeriodData.model_validate({"list": {"2026": [{"ID": "76"}]}})


async def test_domain_scoped_cookies_csrf_and_borrowed_query_defaults():
    calls = []

    def handler(request):
        calls.append(request)
        expected = "www-token" if request.url.host == "www.bilibili.com" else "api-token"
        assert request.headers["cookie"] == f"bili_jct={expected}"
        if request.method == "POST":
            assert dict(request.url.params) == {}
            form = dict(parse_qsl(request.content.decode()))
            assert form["csrf"] == expected
            if request.url.host == "www.bilibili.com":
                return httpx.Response(200, json={"code": 0, "data": "ok"})
            return httpx.Response(200, json={"code": 0, "data": {"prompt": False}})
        assert dict(request.url.params) == {"list_type": "1", "csrf": "api-token"}
        return httpx.Response(200, json={"code": 0, "data": {"list": {}}})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), params={"extra": "wrong"}
    ) as http:
        http.cookies.set("bili_jct", "www-token", domain="www.bilibili.com", path="/")
        http.cookies.set("bili_jct", "api-token", domain="api.bilibili.com", path="/")
        async with AsyncBpiClient(http_client=http) as client:
            assert await client.audio.coin(sid=1, multiply=1) == "ok"
            await client.audio.favorite(rid=1, add_media_ids=["2"])
            assert (await client.audio.rank_period(list_type=1)).list == {}
        assert not http.is_closed
    assert len(calls) == 3


async def test_csrf_refresh_and_wrong_domain_isolation():
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/lyric"):
            return httpx.Response(
                200,
                json={"code": 0, "data": "lyrics"},
                headers={"set-cookie": "bili_jct=renewed; Path=/; Secure"},
            )
        assert dict(parse_qsl(request.content.decode())) == {
            "sid": "1",
            "multiply": "1",
            "csrf": "renewed",
        }
        return httpx.Response(200, json={"code": 0, "data": "ok"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        http.cookies.set("bili_jct", "old", domain="www.bilibili.com", path="/")
        async with AsyncBpiClient(http_client=http) as client:
            await client.audio.lyric(sid=1)
            await client.audio.coin(sid=1, multiply=1)
            with pytest.raises(AuthenticationError):
                await client.audio.favorite(rid=1, add_media_ids=["2"])
    assert len(calls) == 2


async def test_subscription_omits_unset_list_and_favorite_omits_unset_add():
    calls = []

    def handler(request):
        calls.append(request)
        form = dict(parse_qsl(request.content.decode()))
        if request.url.path.endswith("/update"):
            assert form == {"state": "1", "csrf": "token"}
            return httpx.Response(200, json={"code": 0})
        assert form == {"rid": "1", "type": "12", "del_media_ids": "2", "csrf": "token"}
        return httpx.Response(200, json={"code": 0, "data": {"prompt": True}})

    async with AsyncBpiClient(
        cookie="bili_jct=token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await client.audio.subscribe_rank(state=1) is None
        assert (await client.audio.favorite(rid=1, del_media_ids=["2"])).prompt
    assert len(calls) == 2


async def test_www_redirect_not_followed_and_closed_rank_not_treated_as_anonymous():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(302, headers={"location": "https://api.bilibili.com/redirect-target"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), follow_redirects=True
    ) as http:
        async with AsyncBpiClient(http_client=http) as client:
            with pytest.raises(HttpStatusError):
                await client.audio.lyric(sid=1)
        with pytest.raises(ClientClosedError):
            await client.audio.rank_period(list_type=1)
    assert len(calls) == 1


async def test_unreviewed_host_rejected_before_transport():
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client._send("GET", "/", {}, host="example.invalid")
        with pytest.raises(InvalidParameterError):
            client._csrf(host="example.invalid", optional=True)


def test_complete_audio_module_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {m["name"] for m in inventory["methods"] if m["domain"] == "audio"}
    implemented = {
        m["python"].rsplit(".", 1)[1]
        for m in mapping["apis"]
        if m["python"].startswith("AsyncBpiClient.audio.") and m["status"] == "implemented"
    }
    assert len(expected) == 20
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(AudioClient, name, None)) for name in expected)
