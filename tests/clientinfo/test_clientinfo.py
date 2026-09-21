from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import httpx
import pytest

from bpi import AsyncBpiClient, InvalidParameterError
from bpi.clientinfo import ClientInfoClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
IP_FIXTURES = FIXTURES / "clientinfo/ip"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("clientinfo tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_ip_promoted_contract(profile):
    contract = json.loads((IP_FIXTURES / "contract.json").read_bytes())
    body = (IP_FIXTURES / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        data = await client.clientinfo.ip(ip="8.8.8.8")
        assert data.addr == "8.8.8.8"
        assert data.isp == "Google LLC"


async def test_ip_without_argument_has_empty_query():
    def handler(request: httpx.Request) -> httpx.Response:
        assert not request.url.params
        return httpx.Response(
            200,
            json={"code": 0, "data": {"country": None, "addr": None}},
        )

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        data = await client.clientinfo.ip()
        assert data.addr is None


async def test_ip_normalizes_ipv6():
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.url.params))
        return httpx.Response(200, json={"code": 0, "data": {}})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        await client.clientinfo.ip(ip=" 2001:4860:4860:0:0:0:0:8888 ")
    assert seen == {"ip": "2001:4860:4860::8888"}


@pytest.mark.parametrize("ip", ["not-an-ip", "", 123])
async def test_invalid_ip_fails_before_network(ip):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.clientinfo.ip(ip=ip)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("clientinfo/")]
    assert len(paths) == 4
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_clientinfo_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {
        method["name"] for method in inventory["methods"] if method["domain"] == "clientinfo"
    }
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.clientinfo.") and api["status"] == "implemented"
    }
    assert expected == {"ip"}
    assert implemented == expected
    assert inspect.iscoroutinefunction(ClientInfoClient.ip)
