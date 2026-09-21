"""Bangumi module coverage and manual protocol behavior; all tests are offline."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest
from pydantic import ValidationError

from bpi import ApiError, AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi._generated.bangumi_models import BangumiDetailResult, BangumiSectionResult, BangumiStat
from bpi.bangumi.client import BangumiClient
from bpi.bangumi.models import BangumiFollowResult, BangumiVideoStreamData, VipLabel
from bpi.errors import ResponseDecodeError

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Bangumi tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def response(rel: str) -> bytes:
    return (FIXTURES / rel).read_bytes()


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"season_id": 1172}, {"season_id": "1172"}),
        ({"ep_id": 21265}, {"ep_id": "21265"}),
    ],
)
async def test_detail_general_entry_uses_exactly_one_source_id(kwargs, expected):
    body = response("bangumi/info/season-detail-season/responses/anonymous.success.json")

    def handler(request):
        assert request.url.path == "/pgc/view/web/season"
        assert dict(request.url.params) == expected
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.bangumi.detail(**kwargs)
        assert isinstance(result, BangumiDetailResult)
        assert result.season_id == 1172


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"season_id": 1, "ep_id": 2}, {"season_id": 0}, {"ep_id": 0}, {"ep_id": True}],
)
async def test_detail_invalid_ids_fail_before_network(kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.bangumi.detail(**kwargs)


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        (
            {"ep_id": 21265, "quality": 32, "format_flags": 16},
            {"fnver": "0", "ep_id": "21265", "qn": "32", "fnval": "16"},
        ),
        (
            {"cid": 91549662, "quality": 120, "format_flags": 16 | 128},
            {"fnver": "0", "cid": "91549662", "qn": "120", "fnval": "144", "fourk": "1"},
        ),
        (
            {"ep_id": 21265, "format_flags": 16 | 1024},
            {"fnver": "0", "ep_id": "21265", "fnval": "1040", "fourk": "1"},
        ),
    ],
)
async def test_video_stream_protocol_and_fourk_flag(kwargs, expected):
    body = response("bangumi/playurl/responses/anonymous.success.json")

    def handler(request):
        assert request.url.path == "/pgc/player/web/playurl"
        assert dict(request.url.params) == expected
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.bangumi.video_stream(**kwargs)
        assert isinstance(result, BangumiVideoStreamData)
        assert result.quality == 32 and result.dash is not None


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_video_stream_promoted_profiles(profile):
    body = response(f"bangumi/playurl/responses/{profile}.success.json")

    def handler(request):
        assert request.url.path == "/pgc/player/web/playurl"
        assert dict(request.url.params) == {
            "fnver": "0",
            "ep_id": "21265",
            "qn": "32",
            "fnval": "16",
        }
        assert ("SESSDATA=fake" in request.headers.get("cookie", "")) is (profile != "anonymous")
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake" if profile != "anonymous" else None,
        transport=httpx.MockTransport(handler),
    ) as client:
        value = await client.bangumi.video_stream(ep_id=21265, quality=32, format_flags=16)
        assert value.quality == 32 and value.dash is not None


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"ep_id": 1, "cid": 2},
        {"ep_id": 0},
        {"cid": False},
        {"ep_id": 1, "quality": True},
        {"ep_id": 1, "format_flags": -1},
    ],
)
async def test_video_stream_invalid_arguments_fail_before_network(kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.bangumi.video_stream(**kwargs)


@pytest.mark.parametrize(
    "name,path",
    [("follow", "/pgc/web/follow/add"), ("unfollow", "/pgc/web/follow/del")],
)
@pytest.mark.parametrize("response_kind", ["success", "error", "malformed"])
async def test_follow_protocol_is_source_derived(name, path, response_kind):
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "POST" and request.url.path == path
        assert dict(parse_qsl(request.content.decode())) == {
            "season_id": "1172",
            "csrf": "token",
        }
        assert "bili_jct=token" in request.headers["cookie"]
        if response_kind == "error":
            return httpx.Response(200, json={"code": -403, "message": "denied"})
        if response_kind == "malformed":
            return httpx.Response(200, content=b"private-marker")
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {"fmid": 1172, "relation": name == "follow", "status": 1, "toast": "ok"},
            },
        )

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=token", transport=httpx.MockTransport(handler)
    ) as client:
        method = getattr(client.bangumi, name)
        if response_kind == "error":
            with pytest.raises(ApiError) as error:
                await method(season_id=1172)
            assert error.value.code == -403
        elif response_kind == "malformed":
            with pytest.raises(ResponseDecodeError) as error:
                await method(season_id=1172)
            assert error.value.response_body == b"private-marker"
            assert "private-marker" not in str(error.value)
        else:
            result = await method(season_id=1172)
            assert isinstance(result, BangumiFollowResult)
            assert result.relation is (name == "follow")
    assert len(calls) == 1


@pytest.mark.parametrize("name", ["follow", "unfollow"])
async def test_follow_requires_csrf_before_network(name):
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.bangumi, name)(season_id=1172)


@pytest.mark.parametrize("name", ["follow", "unfollow"])
async def test_follow_rejects_invalid_season_id(name):
    async with AsyncBpiClient(cookie="bili_jct=token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.bangumi, name)(season_id=True)


def test_default_models_match_rust_default_semantics():
    stat = BangumiStat.model_validate({"coin": 1, "danmakus": 2, "likes": 3, "play": 4})
    assert stat.coins == 1 and stat.views == 4
    assert stat.favorite == 0 and stat.follow_text == ""
    sections = BangumiSectionResult.model_validate({"section": []})
    assert sections.main_section.id == 0 and sections.main_section.episodes == []
    label = VipLabel.model_validate({})
    assert label.text == "" and label.bg_style == 0


def test_detail_negative_total_and_strict_types():
    body = json.loads(
        response("bangumi/info/season-detail-season/responses/anonymous.success.json")
    )
    payload = body.get("result", body.get("data"))
    payload["total"] = -1
    assert BangumiDetailResult.model_validate(payload).total == -1
    payload["total"] = "-1"
    with pytest.raises(ValidationError):
        BangumiDetailResult.model_validate(payload)


def test_bangumi_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [p for p in provenance["sha256"] if p.startswith("bangumi/")]
    assert paths
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_bangumi_module_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {m["name"] for m in inventory["methods"] if m["domain"] == "bangumi"}
    implemented = {
        m["python"].rsplit(".", 1)[1]
        for m in mapping["apis"]
        if m["python"].startswith("AsyncBpiClient.bangumi.") and m["status"] == "implemented"
    }
    assert len(expected) == 9
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(BangumiClient, name, None)) for name in expected)
