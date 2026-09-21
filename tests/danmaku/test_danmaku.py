from __future__ import annotations

import base64
import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.danmaku import DanmakuClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
DANMAKU_FIXTURES = FIXTURES / "danmaku/read"

WBI_IMG_KEY = "7cd084941338484aae1ad9425b84077c"
WBI_SUB_KEY = "4932caff0ff746eab6f01bf08b70ac45"
CLOCK = 1_700_000_000.0


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("danmaku tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def _contract(path: str) -> dict[str, object]:
    return json.loads((DANMAKU_FIXTURES / path / "contract.json").read_bytes())


def _response(path: str, filename: str) -> bytes:
    return (DANMAKU_FIXTURES / path / "responses" / filename).read_bytes()


def _binary(path: str, filename: str) -> tuple[bytes, str | None]:
    fixture = json.loads(_response(path, filename))
    assert fixture["kind"] == "binary"
    assert fixture["encoding"] == "base64"
    body = base64.b64decode(fixture["body_base64"])
    assert len(body) == fixture["length"]
    return body, fixture.get("content_type")


def _seed_wbi(client: AsyncBpiClient) -> None:
    client._keys = (WBI_IMG_KEY, WBI_SUB_KEY)
    client._bucket = int(CLOCK) // 3600


@pytest.mark.parametrize("profile", ["normal", "vip"])
async def test_history_dates_promoted_contract(profile: str):
    contract = _contract("json-read/history-dates")
    body = _response("json-read/history-dates", f"{profile}.success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.danmaku.history_dates(oid=772096113, month="2022-01")
    assert result is None


async def test_history_dates_anonymous_requires_login():
    body = _response("json-read/history-dates", "anonymous.requires_login.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AuthenticationError):
            await client.danmaku.history_dates(oid=772096113, month="2022-01")


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_snapshot_promoted_contract(profile: str):
    contract = _contract("json-read/snapshot")
    body = _response("json-read/snapshot", f"{profile}.success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        assert await client.danmaku.snapshot(bvid="BV1fK4y1t741") == []


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_thumbup_stats_promoted_contract(profile: str):
    contract = _contract("json-read/thumbup-stats")
    body = _response("json-read/thumbup-stats", f"{profile}.success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        result = await client.danmaku.thumbup_stats(oid=413195701, ids=[1932011031958944000])
    assert result["1932011031958944000"].id_str == "1932011031958944000"


@pytest.mark.parametrize("profile", ["normal", "vip"])
async def test_adv_state_promoted_contract(profile: str):
    contract = _contract("json-read/adv-state")
    body = _response("json-read/adv-state", f"{profile}.success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.danmaku.adv_state(cid=413195701)
    assert result.accept is True
    assert result.coins == 2
    assert result.has_buy is (profile == "vip")


async def test_adv_state_anonymous_requires_login():
    body = _response("json-read/adv-state", "anonymous.requires_login.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AuthenticationError):
            await client.danmaku.adv_state(cid=413195701)


@pytest.mark.parametrize(
    "fixture_path,method,kwargs",
    [
        (
            "non-json-read/web-seg",
            "web_seg_proto",
            {"danmaku_type": 1, "oid": 16546, "segment_index": 1},
        ),
        (
            "non-json-read/mobile-seg",
            "mobile_seg_proto",
            {"danmaku_type": 1, "oid": 16546, "segment_index": 1},
        ),
        (
            "non-json-read/web-view",
            "web_view_proto",
            {"danmaku_type": 1, "oid": 16546},
        ),
    ],
)
@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_promoted_binary_reads(
    fixture_path: str, method: str, kwargs: dict[str, int], profile: str
):
    contract = _contract(fixture_path)
    expected, content_type = _binary(fixture_path, f"{profile}.success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        headers = {} if content_type is None else {"content-type": content_type}
        return httpx.Response(200, stream=httpx.ByteStream(expected), headers=headers)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        result = await getattr(client.danmaku, method)(**kwargs)
    assert result == expected


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_web_seg_wbi_promoted_contract(profile: str):
    contract = _contract("non-json-read/web-seg-wbi")
    expected, content_type = _binary("non-json-read/web-seg-wbi", f"{profile}.success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        base = contract["request"]["query"]
        assert all(request.url.params[key] == value for key, value in base.items())
        assert request.url.params.get("wts")
        assert request.url.params.get("w_rid")
        headers = {} if content_type is None else {"content-type": content_type}
        return httpx.Response(200, content=expected, headers=headers)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(
        cookie=cookie, transport=httpx.MockTransport(handler), clock=lambda: CLOCK
    ) as client:
        _seed_wbi(client)
        result = await client.danmaku.web_seg_wbi_proto(danmaku_type=1, oid=16546, segment_index=1)
    assert result == expected


@pytest.mark.parametrize("profile", ["normal", "vip"])
async def test_web_history_segment_binary_contract(profile: str):
    contract = _contract("non-json-read/web-history-seg")
    expected, content_type = _binary("non-json-read/web-history-seg", f"{profile}.success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == contract["request"]["query"]
        headers = {} if content_type is None else {"content-type": content_type}
        return httpx.Response(200, content=expected, headers=headers)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.danmaku.web_history_seg_proto(
            danmaku_type=1, oid=16546, date="2022-01-01"
        )
    assert result == expected


async def test_raw_binary_read_preserves_anonymous_api_error_body():
    expected = _response("non-json-read/web-history-seg", "anonymous.requires_login.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=expected)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.danmaku.web_history_seg_proto(
            danmaku_type=1, oid=16546, date="2022-01-01"
        )
    assert result == expected


@pytest.mark.parametrize("profile", ["normal", "vip"])
async def test_history_xml_preserves_raw_deflate_bytes(profile: str):
    contract = _contract("history-xml")
    expected, content_type = _binary("history-xml", f"{profile}.success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == contract["request"]["query"]
        headers = {"content-encoding": "deflate"}
        if content_type is not None:
            headers["content-type"] = content_type
        return httpx.Response(200, stream=httpx.ByteStream(expected), headers=headers)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.danmaku.history_xml_bytes(
            danmaku_type=1, oid=16546, date="2022-01-01"
        )
    assert result == expected


async def test_history_xml_anonymous_preserves_error_body():
    expected = _response("history-xml", "anonymous.requires_login.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=httpx.ByteStream(expected))

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.danmaku.history_xml_bytes(
            danmaku_type=1, oid=16546, date="2022-01-01"
        )
    assert result == expected


@pytest.mark.parametrize(
    "fixture_path,method",
    [("xml-read/list-so", "xml_list_so"), ("xml-read/comment-xml", "xml_list")],
)
async def test_xml_reads_parse_promoted_deflate_fixture(fixture_path: str, method: str):
    contract = _contract(fixture_path)
    expected, content_type = _binary(fixture_path, "success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"].get("query", {})
        headers = {"content-encoding": "deflate"}
        if content_type is not None:
            headers["content-type"] = content_type
        return httpx.Response(200, stream=httpx.ByteStream(expected), headers=headers)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await getattr(client.danmaku, method)(cid=16546)
    assert result.chatid == "16546"
    assert len(result.danmakus) == 307
    assert result.danmakus[0].meta.dmid >= 0


async def test_send_source_derived_signed_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/v2/dm/post"
        form = parse_qs(request.content.decode(), keep_blank_values=True)
        assert form["type"] == ["1"]
        assert form["oid"] == ["413195701"]
        assert form["msg"] == ["  hello  "]
        assert form["mode"] == ["1"]
        assert form["fontsize"] == ["25"]
        assert form["color"] == ["16777215"]
        assert form["pool"] == ["0"]
        assert form["progress"] == ["1878"]
        assert form["rnd"] == ["2"]
        assert form["plat"] == ["1"]
        assert form["csrf"] == ["csrf-token"]
        assert form["checkbox_type"] == ["0"]
        assert form["colorful"] == [""]
        assert form["gaiasource"] == ["main_web"]
        assert form["polaris_app_id"] == ["100"]
        assert form["polaris_platform"] == ["5"]
        assert form["spmid"] == ["333.788.0.0"]
        assert form["from_spmid"] == ["333.788.0.0"]
        assert form["avid"] == ["170001"]
        assert form["bvid"] == ["BV1fK4y1t741"]
        assert form["wts"]
        assert form["w_rid"]
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {"colorful_src": None, "dmid": 9, "dmid_str": "9"},
            },
        )

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
        clock=lambda: CLOCK,
    ) as client:
        _seed_wbi(client)
        result = await client.danmaku.send(
            oid=413195701,
            msg="  hello  ",
            aid=170001,
            bvid="BV1fK4y1t741",
        )
    assert result.dmid == 9


@pytest.mark.parametrize(
    "method,path,kwargs,expected",
    [
        (
            "recall",
            "/x/dm/recall",
            {"cid": 413195701, "dmid": 1932011031958944000},
            {"cid": ["413195701"], "dmid": ["1932011031958944000"], "type": ["1"]},
        ),
        ("buy_adv", "/x/dm/adv/buy", {"cid": 413195701}, {"cid": ["413195701"], "mode": ["sp"]}),
        (
            "thumbup",
            "/x/v2/dm/thumbup/add",
            {"oid": 413195701, "dmid": 1932011031958944000, "op": 1},
            {
                "oid": ["413195701"],
                "dmid": ["1932011031958944000"],
                "op": ["1"],
                "platform": ["web_player"],
            },
        ),
        (
            "report",
            "/x/dm/report/add",
            {"cid": 413195701, "dmid": 1932011031958944000, "reason": 2, "content": " details "},
            {
                "cid": ["413195701"],
                "dmid": ["1932011031958944000"],
                "reason": ["2"],
                "content": ["details"],
            },
        ),
        (
            "edit_state",
            "/x/v2/dm/edit/state",
            {"oid": 413195701, "dmids": [10, 20], "state": 1},
            {"type": ["1"], "oid": ["413195701"], "dmids": ["10,20"], "state": ["1"]},
        ),
        (
            "edit_pool",
            "/x/v2/dm/edit/pool",
            {"oid": 413195701, "dmids": [10, 20], "pool": 2},
            {"type": ["1"], "oid": ["413195701"], "dmids": ["10,20"], "pool": ["2"]},
        ),
    ],
)
async def test_source_derived_write_forms(
    method: str, path: str, kwargs: dict[str, object], expected: dict[str, list[str]]
):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == path
        form = parse_qs(request.content.decode(), keep_blank_values=True)
        assert form == {**expected, "csrf": ["csrf-token"]}
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        result = await getattr(client.danmaku, method)(**kwargs)
    assert result is None


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("history_dates", {"oid": 1, "month": "2022-13"}),
        ("history_dates", {"oid": 1, "month": "2022-01", "danmaku_type": 0}),
        ("snapshot", {}),
        ("snapshot", {"aid": 1, "bvid": "BV1fK4y1t741"}),
        ("thumbup_stats", {"oid": 1, "ids": []}),
        ("thumbup_stats", {"oid": 1, "ids": [0]}),
        ("web_seg_proto", {"danmaku_type": 0, "oid": 1, "segment_index": 1}),
        ("web_seg_proto", {"danmaku_type": 1, "oid": 1, "segment_index": 0}),
        (
            "web_seg_proto",
            {"danmaku_type": 1, "oid": 1, "segment_index": 1, "ps": 10},
        ),
        (
            "web_seg_proto",
            {"danmaku_type": 1, "oid": 1, "segment_index": 1, "ps": 10, "pe": 9},
        ),
        ("history_xml_bytes", {"danmaku_type": 1, "oid": 1, "date": "2022-13-01"}),
        ("send", {"oid": 1, "msg": "   "}),
        ("thumbup", {"oid": 1, "dmid": 1, "op": 3}),
        ("report", {"cid": 1, "dmid": 1, "reason": 1, "content": "   "}),
        ("edit_state", {"oid": 1, "dmids": [], "state": 1}),
        ("edit_pool", {"oid": 1, "dmids": [0], "pool": 1}),
    ],
)
async def test_invalid_arguments_fail_before_network(method: str, kwargs: dict[str, object]):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.danmaku, method)(**kwargs)


async def test_write_requires_csrf_after_validation():
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await client.danmaku.recall(cid=1, dmid=1)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("danmaku/read/")]
    assert len(paths) == 44
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_danmaku_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "danmaku"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.danmaku.") and api["status"] == "implemented"
    }
    assert len(expected) == 19
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(DanmakuClient, name, None)) for name in expected)
