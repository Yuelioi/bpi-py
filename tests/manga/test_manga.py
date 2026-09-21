from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import AsyncBpiClient, HttpStatusError, InvalidParameterError
from bpi.manga import MangaClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
MANGA_FIXTURES = FIXTURES / "manga/read"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("manga tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


READ_CASES = [
    ("season-info", "season_info", {}, "success.json", None),
    ("clock-in-info", "clock_in_info", {}, "success.json", None),
    ("user-point", "user_point", {}, "success.json", None),
    ("point-products", "point_products", {}, "success.json", None),
    (
        "coupons",
        "coupons",
        {"page_num": 1, "page_size": 20},
        "authenticated.success.json",
        "SESSDATA=fake",
    ),
]


@pytest.mark.parametrize(
    "endpoint,method,kwargs,response_file,cookie",
    READ_CASES,
    ids=[case[0] for case in READ_CASES],
)
async def test_promoted_read_contracts(endpoint, method, kwargs, response_file, cookie):
    fixture_dir = MANGA_FIXTURES / endpoint
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / "responses" / response_file).read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        if "body" in contract["request"]:
            assert json.loads(request.content) == contract["request"]["body"]
        else:
            assert request.content == b""
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        result = await getattr(client.manga, method)(**kwargs)

    assert result is not None


async def test_coupons_anonymous_http_401_retains_requires_login_semantics():
    body = (MANGA_FIXTURES / "coupons/responses/anonymous.requires_login.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(HttpStatusError) as exc_info:
            await client.manga.coupons(page_num=1, page_size=20)

    assert exc_info.value.status_code == 401
    assert exc_info.value.requires_login()


async def test_clock_in_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/twirp/activity.v1.Activity/ClockIn"
        assert parse_qs(request.content.decode()) == {"platform": ["android"]}
        return httpx.Response(200, json={"code": 0, "data": {"status": 1}})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.manga.manga_clock_in()
    assert result == {"status": 1}


async def test_clock_in_makeup_source_derived_json():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/twirp/activity.v1.Activity/ClockIn"
        assert dict(request.url.params) == {"platform": "android"}
        assert json.loads(request.content) == {"type": 0, "date": "2026-09-20"}
        return httpx.Response(200, json={"code": 0, "data": {}})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        assert await client.manga.manga_clock_in_makeup(date="2026-09-20") == {}


async def test_share_comic_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/twirp/activity.v1.Activity/ShareComic"
        assert parse_qs(request.content.decode()) == {"platform": ["android"]}
        return httpx.Response(200, json={"code": 0, "data": {"point": 10}})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.manga.manga_share_comic()
    assert result.point == 10


@pytest.mark.parametrize(
    "method,kwargs,expected",
    [
        (
            "manga_buy_episode",
            {
                "ep_id": 11,
                "buy_method": 2,
                "coupon_id": 22,
                "auto_pay_gold_status": 2,
                "is_presale": 0,
            },
            {
                "epId": 11,
                "buyMethod": 2,
                "couponId": 22,
                "autoPayGoldStatus": 2,
                "isPresale": 0,
            },
        ),
        (
            "manga_buy_episode_with_coupon",
            {"ep_id": 11, "coupon_id": 22},
            {
                "epId": 11,
                "buyMethod": 2,
                "couponId": 22,
                "autoPayGoldStatus": 2,
                "isPresale": 0,
            },
        ),
        (
            "manga_buy_episode_with_free",
            {"comic_id": 33, "ep_id": 11},
            {"epId": 11, "buyMethod": 4, "couponId": 0, "comicId": 33},
        ),
        (
            "manga_buy_episode_with_general_coupon",
            {"ep_id": 11, "pay_amount": 44},
            {
                "epId": 11,
                "buyMethod": 5,
                "couponId": 0,
                "autoPayGoldStatus": 2,
                "isPresale": 0,
                "payAmount": 44,
            },
        ),
    ],
)
async def test_buy_episode_source_derived_json(method, kwargs, expected):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/twirp/comic.v1.Comic/BuyEpisode"
        assert dict(request.url.params) == {"platform": "web"}
        assert json.loads(request.content) == expected
        return httpx.Response(200, json={"code": 0, "data": {}})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        assert await getattr(client.manga, method)(**kwargs) == {}


async def test_point_exchange_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/twirp/pointshop.v1.Pointshop/Exchange"
        assert parse_qs(request.content.decode()) == {
            "product_id": ["1938"],
            "product_num": ["2"],
            "point": ["100"],
        }
        return httpx.Response(200, json={"code": 0, "data": {}})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.manga.manga_point_exchange(product_id=1938, product_num=2, point=100)
    assert result == {}


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("coupons", {"page_num": 0, "page_size": 20}),
        ("coupons", {"page_num": 1, "page_size": 101}),
        ("manga_clock_in_makeup", {"date": "2026/09/20"}),
        (
            "manga_buy_episode",
            {"ep_id": 0, "buy_method": 2, "coupon_id": 1},
        ),
        ("manga_buy_episode_with_coupon", {"ep_id": 1, "coupon_id": -1}),
        ("manga_buy_episode_with_free", {"comic_id": 0, "ep_id": 1}),
        (
            "manga_buy_episode_with_general_coupon",
            {"ep_id": 1, "pay_amount": -1},
        ),
        ("manga_point_exchange", {"product_id": 0, "product_num": 1, "point": 0}),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.manga, method)(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("manga/")]
    assert len(paths) == 11
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_manga_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "manga"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.manga.") and api["status"] == "implemented"
    }
    assert len(expected) == 13
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(MangaClient, name, None)) for name in expected)
