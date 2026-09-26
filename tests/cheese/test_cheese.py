"""Cheese/PUGV module coverage; all requests use offline contract fixtures."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from bpi import AsyncBpiClient, InvalidParameterError
from bpi._generated.cheese_models import CourseInfo, CoursePayment
from bpi.cheese.client import CheeseClient
from bpi.cheese.models import CourseVideoStreamData

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
LIVE_SHAPE_FIXTURES = ROOT / "tests/cheese/fixtures"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Cheese tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def response(rel: str) -> bytes:
    return (FIXTURES / rel).read_bytes()


@pytest.mark.parametrize(
    "kwargs,fixture,expected_query",
    [
        (
            {"season_id": 556},
            "cheese/info/season-detail-season/responses/anonymous.success.json",
            {"season_id": "556"},
        ),
        (
            {"ep_id": 20767},
            "cheese/info/season-detail-episode/responses/anonymous.success.json",
            {"ep_id": "20767"},
        ),
    ],
)
async def test_info_general_entry_uses_exactly_one_source_id(kwargs, fixture, expected_query):
    def handler(request):
        assert request.url.path == "/pugv/view/web/season"
        assert dict(request.url.params) == expected_query
        return httpx.Response(200, content=response(fixture))

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.cheese.info(**kwargs)
        assert isinstance(result, CourseInfo)
        assert result.season_id == 556
        assert result.episode_page.total == 603 and result.episodes


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"season_id": 1, "ep_id": 2}, {"season_id": 0}, {"ep_id": 0}, {"ep_id": True}],
)
async def test_info_invalid_ids_fail_before_network(kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.cheese.info(**kwargs)


async def test_ep_list_can_omit_optional_pagination():
    body = response("cheese/info/ep-list/responses/anonymous.success.json")

    def handler(request):
        assert request.url.path == "/pugv/view/web/ep/list"
        assert dict(request.url.params) == {"season_id": "556"}
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.cheese.ep_list(season_id=556)
        assert result.page.total == 603 and result.items


@pytest.mark.parametrize(
    "kwargs",
    [
        {"season_id": 0},
        {"season_id": True},
        {"season_id": 556, "page_size": 0},
        {"season_id": 556, "page_size": True},
        {"season_id": 556, "page": 0},
    ],
)
async def test_ep_list_invalid_parameters_fail_before_network(kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.cheese.ep_list(**kwargs)


@pytest.mark.parametrize(
    "quality,format_flags,expected_extra",
    [
        (32, 16, {"qn": "32", "fnval": "16"}),
        (120, 16 | 128, {"qn": "120", "fnval": "144", "fourk": "1"}),
        (None, 16 | 1024, {"fnval": "1040", "fourk": "1"}),
    ],
)
async def test_video_stream_protocol_and_fourk_flag(quality, format_flags, expected_extra):
    body = response("cheese/playurl/responses/anonymous.success.json")

    def handler(request):
        expected = {
            "avid": "997984154",
            "ep_id": "163956",
            "cid": "1183682680",
            "fnver": "0",
            **expected_extra,
        }
        assert request.url.path == "/pugv/player/web/playurl"
        assert dict(request.url.params) == expected
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.cheese.video_stream(
            aid=997984154,
            ep_id=163956,
            cid=1183682680,
            quality=quality,
            format_flags=format_flags,
        )
        assert isinstance(result, CourseVideoStreamData)
        assert result.quality == 32 and result.dash is not None


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_video_stream_promoted_profiles(profile):
    body = response(f"cheese/playurl/responses/{profile}.success.json")

    def handler(request):
        assert dict(request.url.params) == {
            "avid": "997984154",
            "ep_id": "163956",
            "cid": "1183682680",
            "fnver": "0",
            "qn": "32",
            "fnval": "16",
        }
        assert ("SESSDATA=fake" in request.headers.get("cookie", "")) is (profile != "anonymous")
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake" if profile != "anonymous" else None,
        transport=httpx.MockTransport(handler),
    ) as client:
        value = await client.cheese.video_stream(
            aid=997984154, ep_id=163956, cid=1183682680, quality=32, format_flags=16
        )
        assert value.quality == 32 and value.has_paid is False and value.dash is not None
        assert (
            value.dash.video[0].base_url == "https://example.invalid/bilibili/playurl/redacted.m4s"
        )
        assert value.fragment_videos
        assert "32" in value.fragment_videos[0].video_info.file_info


@pytest.mark.parametrize(
    "kwargs",
    [
        {"aid": 0, "ep_id": 1, "cid": 1},
        {"aid": 1, "ep_id": 0, "cid": 1},
        {"aid": 1, "ep_id": 1, "cid": 0},
        {"aid": True, "ep_id": 1, "cid": 1},
        {"aid": 1, "ep_id": 1, "cid": 1, "quality": 0},
        {"aid": 1, "ep_id": 1, "cid": 1, "format_flags": False},
    ],
)
async def test_video_stream_invalid_arguments_fail_before_network(kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.cheese.video_stream(**kwargs)


def test_generated_defaults_and_strict_types_match_rust():
    payment = CoursePayment.model_validate(
        {"desc": "", "discount_desc": "", "pay_shade": "", "price": 1.0, "price_format": "1"}
    )
    assert payment.discount_prefix == ""
    with pytest.raises(ValidationError):
        CoursePayment.model_validate(
            {"desc": "", "discount_desc": "", "pay_shade": "", "price": "1", "price_format": "1"}
        )


def test_course_without_coupon_or_discount_decodes():
    payload = json.loads((LIVE_SHAPE_FIXTURES / "no-coupon.sanitized.json").read_bytes())["data"]
    value = CourseInfo.model_validate(payload)
    assert value.season_id == 877726892
    assert len(value.episodes) == 7
    assert value.coupon is None
    assert value.payment.discount_desc == ""


def test_drm_course_decodes_without_accept_fields_and_preserves_metadata():
    payload = json.loads(
        (LIVE_SHAPE_FIXTURES / "drm.anonymous.sanitized.json").read_bytes()
    )["data"]
    value = CourseVideoStreamData.model_validate(payload)
    assert value.accept_quality == []
    assert value.accept_format == ""
    assert value.accept_description == []
    assert value.is_drm is True
    assert value.drm_type == "bili_drm"
    assert value.drm_tech_type == 3
    assert value.hls is not None
    assert value.hls.video[0].id == 120
    assert value.hls.audio[0].id == 100010


def test_preview_course_preserves_direct_stream_and_preview_flag():
    payload = json.loads(
        (LIVE_SHAPE_FIXTURES / "preview.anonymous.sanitized.json").read_bytes()
    )["data"]
    value = CourseVideoStreamData.model_validate(payload)
    assert value.is_preview == 1
    assert value.has_paid is False
    assert value.dash is None
    assert value.durl is not None
    assert value.durl[0].url == "https://example.invalid/preview.mp4"


def test_cheese_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [p for p in provenance["sha256"] if p.startswith("cheese/")]
    assert len(paths) == 16
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_cheese_module_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {m["name"] for m in inventory["methods"] if m["domain"] == "cheese"}
    implemented = {
        m["python"].rsplit(".", 1)[1]
        for m in mapping["apis"]
        if m["python"].startswith("AsyncBpiClient.cheese.") and m["status"] == "implemented"
    }
    assert len(expected) == 5
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(CheeseClient, name, None)) for name in expected)
