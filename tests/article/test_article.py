from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import ApiError, AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.article import ArticleClient, ArticleInfoData, ArticlesData, ArticleViewData

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
ARTICLE_FIXTURES = FIXTURES / "article"
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
        raise AssertionError("article tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
@pytest.mark.parametrize(
    ("endpoint", "method", "kwargs"),
    [
        ("info", "info", {"article_id": 2}),
        ("articles", "articles", {"article_list_id": 207146}),
    ],
)
async def test_public_read_promoted_contracts(profile, endpoint, method, kwargs):
    fixture_dir = ARTICLE_FIXTURES / endpoint
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        result = await getattr(client.article, method)(**kwargs)

    if endpoint == "info":
        assert isinstance(result, ArticleInfoData)
        assert result.mid > 0
    else:
        assert isinstance(result, ArticlesData)
        assert result.list.id == 207146


@pytest.mark.parametrize("profile", ["normal", "vip"])
@pytest.mark.parametrize(
    ("endpoint", "method", "kwargs"),
    [
        ("view", "view", {"article_id": 2}),
        ("cards", "cards", {"ids": "av2,cv1,cv2"}),
    ],
)
async def test_wbi_read_promoted_contracts(profile, endpoint, method, kwargs):
    fixture_dir = ARTICLE_FIXTURES / endpoint
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / f"responses/{profile}.success.json").read_bytes()
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path == "/x/web-interface/nav":
            return httpx.Response(200, json=WBI_BODY)
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        actual = dict(request.url.params)
        assert actual.pop("wts") == "1700000000"
        assert len(actual.pop("w_rid")) == 32
        assert actual == contract["request"]["query"]
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake",
        transport=httpx.MockTransport(handler),
        clock=lambda: 1_700_000_000.0,
    ) as client:
        result = await getattr(client.article, method)(**kwargs)

    assert result is not None
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("endpoint", "method", "kwargs"),
    [
        ("view", "view", {"article_id": 2}),
        ("cards", "cards", {"ids": "av2,cv1,cv2"}),
    ],
)
async def test_wbi_anonymous_contract_errors(endpoint, method, kwargs):
    fixture_dir = ARTICLE_FIXTURES / endpoint
    body = (fixture_dir / "responses/anonymous.error.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/x/web-interface/nav":
            return httpx.Response(200, json=WBI_BODY)
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        transport=httpx.MockTransport(handler), clock=lambda: 1_700_000_000.0
    ) as client:
        with pytest.raises(ApiError) as exc_info:
            await getattr(client.article, method)(**kwargs)
    assert exc_info.value.code == -352


async def test_custom_read_params_are_preserved_before_wbi_signing():
    seen: list[dict[str, str]] = []
    view_body = (ARTICLE_FIXTURES / "view/responses/normal.success.json").read_bytes()
    cards_body = (ARTICLE_FIXTURES / "cards/responses/normal.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/x/web-interface/nav":
            return httpx.Response(200, json=WBI_BODY)
        query = dict(request.url.params)
        query.pop("wts")
        query.pop("w_rid")
        seen.append(query)
        body = view_body if request.url.path.endswith("/view") else cards_body
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake",
        transport=httpx.MockTransport(handler),
        clock=lambda: 1_700_000_000.0,
    ) as client:
        view = await client.article.view(article_id=2, gaia_source="article_test")
        cards = await client.article.cards(ids="av2,cv1,cv2", web_location="1.2")

    assert isinstance(view, ArticleViewData)
    assert isinstance(cards, dict)
    assert seen == [
        {"id": "2", "gaia_source": "article_test"},
        {"ids": "av2,cv1,cv2", "web_location": "1.2"},
    ]


@pytest.mark.parametrize(
    ("method", "kwargs", "path", "expected_form", "response"),
    [
        (
            "like",
            {"article_id": 2, "like": True},
            "/x/article/like",
            {"id": ["2"], "type": ["1"], "csrf": ["csrf-token"]},
            {"code": 0},
        ),
        (
            "coin",
            {"aid": 2, "upid": 7792521, "multiply": 2},
            "/x/web-interface/coin/add",
            {
                "aid": ["2"],
                "upid": ["7792521"],
                "multiply": ["2"],
                "avtype": ["2"],
                "csrf": ["csrf-token"],
            },
            {"code": 0, "data": {"like": True}},
        ),
        (
            "favorite",
            {"article_id": 2},
            "/x/article/favorites/add",
            {"id": ["2"], "csrf": ["csrf-token"]},
            {"code": 0, "data": {"ok": True}},
        ),
        (
            "unfavorite",
            {"article_id": 2},
            "/x/article/favorites/del",
            {"id": ["2"], "csrf": ["csrf-token"]},
            {"code": 0, "data": {"ok": True}},
        ),
    ],
)
async def test_source_derived_write_protocol(method, kwargs, path, expected_form, response):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == path
        assert parse_qs(request.content.decode(), keep_blank_values=True) == expected_form
        return httpx.Response(200, json=response)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await getattr(client.article, method)(**kwargs)

    if method == "like":
        assert result is None
    elif method == "coin":
        assert result.like is True
    else:
        assert result == {"ok": True}


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("info", {"article_id": 0}),
        ("articles", {"article_list_id": 0}),
        ("view", {"article_id": 2, "gaia_source": " "}),
        ("cards", {"ids": " "}),
        ("like", {"article_id": 2, "like": 1}),
        ("coin", {"aid": 2, "upid": 7792521, "multiply": 3}),
        ("favorite", {"article_id": 0}),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=csrf-token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.article, method)(**kwargs)


async def test_write_requires_csrf_after_parameter_validation():
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await client.article.favorite(article_id=2)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("article/")]
    assert len(paths) == 16
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_article_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "article"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.article.") and api["status"] == "implemented"
    }
    assert len(expected) == 8
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(ArticleClient, name, None)) for name in expected)
