from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import AsyncBpiClient, InvalidParameterError
from bpi.misc import MiscClient, ShortLinkData, ticket_hexsign

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
MISC_FIXTURES = FIXTURES / "misc"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("misc tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize("endpoint", ["buvid3", "buvid"])
@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_buvid_promoted_contracts(endpoint, profile):
    fixture_dir = MISC_FIXTURES / endpoint
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == contract["request"]["url"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        data = await getattr(client.misc, endpoint)()

    if endpoint == "buvid3":
        assert data.buvid == "BUVID3_SANITIZED"
    else:
        assert data.buvid3 == "BUVID3_SANITIZED"
        assert data.buvid4 == "BUVID4_SANITIZED"


async def test_b23_short_link_promoted_contract_and_extract():
    fixture_dir = MISC_FIXTURES / "b23tv/short-link"
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / "responses/success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == contract["request"]["url"]
        assert parse_qs(request.content.decode()) == {
            key: [value] for key, value in contract["request"]["form"].items()
        }
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        data = await client.misc.b23_short_link(10001)

    assert data.count == 0
    assert data.title == "sanitized-title"
    assert data.link == "https://b23.tv/sanitized"


async def test_b23_short_link_custom_form():
    seen: dict[str, list[str]] = {}
    body = (MISC_FIXTURES / "b23tv/short-link/responses/success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(parse_qs(request.content.decode()))
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        await client.misc.b23_short_link(
            10001,
            platform="web",
            share_channel="WEIXIN",
            share_id="custom.share.id",
            share_mode=5,
            buvid="custom-buvid",
            build=123456,
        )

    assert seen == {
        "platform": ["web"],
        "share_channel": ["WEIXIN"],
        "share_id": ["custom.share.id"],
        "share_mode": ["5"],
        "oid": ["10001"],
        "buvid": ["custom-buvid"],
        "build": ["123456"],
    }


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"aid": 0}, "aid"),
        ({"aid": 1, "buvid": "   "}, "buvid"),
        ({"aid": 1, "share_mode": -1}, "share_mode"),
        ({"aid": 1, "build": True}, "build"),
    ],
)
async def test_b23_short_link_rejects_invalid_params_before_network(kwargs, message):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError, match=message):
            await client.misc.b23_short_link(**kwargs)


@pytest.mark.parametrize(
    ("cookie", "expected_csrf"),
    [(None, ""), ("SESSDATA=fake; bili_jct=csrf-token", "csrf-token")],
)
async def test_bili_ticket_promoted_contract(cookie, expected_csrf):
    fixture_dir = MISC_FIXTURES / "sign/bili-ticket"
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / "responses/success.json").read_bytes()
    timestamp = 1_700_000_000

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == {
            "key_id": "ec02",
            "hexsign": ticket_hexsign(timestamp),
            "context[ts]": str(timestamp),
            "csrf": expected_csrf,
        }
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie=cookie,
        transport=httpx.MockTransport(handler),
        clock=lambda: float(timestamp),
    ) as client:
        data = await client.misc.bili_ticket()

    assert data.created_at == 1_700_000_000
    assert data.ttl == 259_200
    assert data.ticket == "sanitized.header.sanitized-signature"
    assert data.nav.img.startswith("https://")


async def test_bili_ticket_string_delegates_to_ticket_request():
    body = (MISC_FIXTURES / "sign/bili-ticket/responses/success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        transport=httpx.MockTransport(handler), clock=lambda: 1_700_000_000.0
    ) as client:
        assert await client.misc.bili_ticket_string() == "sanitized.header.sanitized-signature"


def test_short_link_without_marker_keeps_content_as_title():
    data = ShortLinkData(content="plain title", count=0)
    data.extract()
    assert data.title == "plain title"
    assert data.link == ""


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("misc/")]
    assert len(paths) == 12
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_misc_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "misc"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.misc.") and api["status"] == "implemented"
    }
    assert expected == {"buvid3", "buvid", "b23_short_link", "bili_ticket", "bili_ticket_string"}
    assert implemented == expected
    assert inspect.iscoroutinefunction(MiscClient.buvid3)
    assert inspect.iscoroutinefunction(MiscClient.buvid)
    assert inspect.iscoroutinefunction(MiscClient.b23_short_link)
    assert inspect.iscoroutinefunction(MiscClient.bili_ticket)
    assert inspect.iscoroutinefunction(MiscClient.bili_ticket_string)
