from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import httpx
import pytest

from bpi import AsyncBpiClient, InvalidParameterError
from bpi.activity import ActivityClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
INFO_FIXTURES = FIXTURES / "activity/info"
LIST_FIXTURES = FIXTURES / "activity/list"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("activity tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_info_promoted_contract(profile):
    contract = json.loads((INFO_FIXTURES / "contract.json").read_bytes())
    body = (INFO_FIXTURES / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        data = await client.activity.info(sid=4_017_552, bvid="BV1mKY4e8ELy")
        assert data.id == 4_017_552
        assert data.lid == 294_258_214


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_list_promoted_contract(profile):
    contract = json.loads((LIST_FIXTURES / "contract.json").read_bytes())
    body = (LIST_FIXTURES / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        data = await client.activity.list(page_size=1)
        assert data.num == 1
        assert data.size == 1
        assert len(data.list) == 1


async def test_info_without_bvid_only_sends_sid():
    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == {"sid": "4017552"}
        return httpx.Response(
            200, content=(INFO_FIXTURES / "responses/anonymous.success.json").read_bytes()
        )

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        await client.activity.info(sid=4_017_552)


async def test_list_default_uses_rust_defaults():
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.url.params))
        return httpx.Response(
            200, json={"code": 0, "data": {"list": [], "num": 1, "size": 15, "total": 0}}
        )

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        data = await client.activity.list_default()
        assert data.size == 15
    assert seen == {"plat": "1,3", "mold": "0", "http": "3", "pn": "1", "ps": "15"}


async def test_list_custom_query():
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.url.params))
        return httpx.Response(
            200, json={"code": 0, "data": {"list": [], "num": 3, "size": 30, "total": 0}}
        )

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        await client.activity.list(platform_filter="1", mold=2, http_mode=4, page=3, page_size=30)
    assert seen == {"plat": "1", "mold": "2", "http": "4", "pn": "3", "ps": "30"}


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("info", {"sid": 0}),
        ("info", {"sid": 1, "bvid": "bad"}),
        ("list", {"platform_filter": " "}),
        ("list", {"page": 0}),
        ("list", {"page_size": 0}),
        ("list", {"mold": -1}),
        ("list", {"http_mode": -1}),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.activity, method)(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("activity/")]
    assert len(paths) == 8
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_activity_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "activity"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.activity.") and api["status"] == "implemented"
    }
    assert expected == {"info", "list", "list_default"}
    assert implemented == expected
    assert inspect.iscoroutinefunction(ActivityClient.info)
    assert inspect.iscoroutinefunction(ActivityClient.list)
    assert inspect.iscoroutinefunction(ActivityClient.list_default)
