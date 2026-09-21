from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from bpi import AsyncBpiClient, InvalidParameterError
from bpi.search import (
    CategoryId,
    Duration,
    OrderSort,
    SearchClient,
    SearchData,
    SearchOrder,
    UserType,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
SEARCH_FIXTURES = FIXTURES / "search"
SIGNED = {
    "search.article",
    "search.bangumi",
    "search.bili_user",
    "search.live",
    "search.live_room",
    "search.live_user",
    "search.movie",
    "search.video",
    "search.default",
}
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
        raise AssertionError("Search tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


CASES = [
    (
        "article",
        "article",
        {
            "keyword": "Rust",
            "order": SearchOrder.PUB_DATE,
            "category_id": CategoryId.TECHNOLOGY,
        },
    ),
    ("bangumi", "bangumi", {"keyword": "天气之子"}),
    (
        "bili-user",
        "bili_user",
        {
            "keyword": "老番茄",
            "order_sort": OrderSort.DESCENDING,
            "user_type": UserType.ALL,
        },
    ),
    ("live", "live", {"keyword": "游戏"}),
    ("live-room", "live_room", {"keyword": "游戏", "order": SearchOrder.ONLINE}),
    (
        "live-user",
        "live_user",
        {
            "keyword": "散人",
            "order_sort": OrderSort.DESCENDING,
            "user_type": UserType.ALL,
        },
    ),
    ("movie", "movie", {"keyword": "哈利波特"}),
    (
        "video",
        "video",
        {
            "keyword": "Rust 教程",
            "order": SearchOrder.ONLINE,
            "duration": Duration.FROM_10_TO_30,
            "tid": 171,
        },
    ),
    ("default", "default", {}),
    ("suggest", "suggest", {"term": "rust"}),
    ("hotwords", "hotwords", {}),
]


@pytest.mark.parametrize("directory,method,kwargs", CASES, ids=[case[0] for case in CASES])
async def test_promoted_contracts_through_public_methods(directory, method, kwargs):
    contract = json.loads((SEARCH_FIXTURES / directory / "contract.json").read_bytes())
    response_path = SEARCH_FIXTURES / directory / contract["cases"][0]["response"]["fixture"]
    body = response_path.read_bytes()
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path == "/x/web-interface/nav":
            return httpx.Response(200, json=WBI_BODY)

        expected = contract["request"]
        assert request.method == expected["method"]
        assert str(request.url).split("?")[0] == expected["url"]
        actual = dict(request.url.params)
        if contract["name"] in SIGNED:
            assert actual.pop("wts", "").isdigit()
            assert len(actual.pop("w_rid", "")) == 32
        assert actual == expected["query"]
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await getattr(client.search, method)(**kwargs)

    assert result is not None
    assert len(calls) == (2 if contract["name"] in SIGNED else 1)


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("article", {"keyword": " "}),
        ("bangumi", {"keyword": "x", "page": 0}),
        ("bili_user", {"keyword": "x", "order_sort": 0}),
        ("live_room", {"keyword": "x", "order": "online"}),
        ("live_user", {"keyword": "x", "user_type": 0}),
        ("video", {"keyword": "x", "duration": 2}),
        ("video", {"keyword": "x", "tid": True}),
        ("suggest", {"term": "\t"}),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.search, method)(**kwargs)


def test_search_models_keep_rust_optional_semantics_and_strictness():
    data = SearchData[list[int]].model_validate(
        {
            "seid": "s",
            "page": 1,
            "pagesize": 20,
            "numResults": 0,
            "numPages": 0,
            "result": [],
        }
    )
    assert data.result == [] and data.page_info is None
    with pytest.raises(ValidationError):
        SearchData[list[int]].model_validate(
            {
                "seid": "s",
                "page": "1",
                "pagesize": 20,
                "numResults": 0,
                "numPages": 0,
                "result": [],
            }
        )


def test_search_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("search/")]
    assert len(paths) == 22
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_search_module_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "search"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.search.") and api["status"] == "implemented"
    }
    assert len(expected) == 11
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(SearchClient, name, None)) for name in expected)
