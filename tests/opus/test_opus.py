from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import httpx
import pytest

from bpi import AsyncBpiClient, InvalidParameterError
from bpi.opus import OpusClient, OpusSpaceFeedKind

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
OPUS_FIXTURES = FIXTURES / "opus/space-read/space-feed"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("opus tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_space_feed_promoted_contract(profile):
    contract = json.loads((OPUS_FIXTURES / "contract.json").read_bytes())
    body = (OPUS_FIXTURES / "responses/success.json").read_bytes()
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        data = await client.opus.space_feed(mid=1000001)
        assert data.items
    assert len(calls) == 1


async def test_space_feed_optional_query():
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.url.params))
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {"has_more": False, "items": [], "offset": "", "update_num": 0},
            },
        )

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        await client.opus.space_feed(
            mid=1000001,
            page=2,
            offset="offset-token",
            kind=OpusSpaceFeedKind.ARTICLE,
        )
    assert seen == {
        "host_mid": "1000001",
        "page": "2",
        "offset": "offset-token",
        "type": "article",
        "web_location": "333.1387",
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mid": 0},
        {"mid": 1, "page": -1},
        {"mid": 1, "offset": " "},
        {"mid": 1, "kind": "invalid"},
    ],
)
async def test_invalid_arguments_fail_before_network(kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.opus.space_feed(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("opus/")]
    assert len(paths) == 2
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_opus_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "opus"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.opus.") and api["status"] == "implemented"
    }
    assert expected == {"space_feed"}
    assert implemented == expected
    assert inspect.iscoroutinefunction(OpusClient.space_feed)
