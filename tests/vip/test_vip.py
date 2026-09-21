from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.vip import Vip, VipClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
CENTER_FIXTURES = FIXTURES / "vip/read/center-info"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("vip tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_center_info_promoted_contract(profile):
    contract = json.loads((CENTER_FIXTURES / "contract.json").read_bytes())
    body = (CENTER_FIXTURES / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        data = await client.vip.center_info()
        if profile == "anonymous":
            assert data.user.account is None
            assert data.user.vip is None
        else:
            assert data.user.account is not None
            assert data.user.vip is not None
            assert data.user.vip.vip_status == (1 if profile == "vip" else 0)


async def test_center_info_custom_build():
    seen: dict[str, str] = {}
    body = (CENTER_FIXTURES / "responses/anonymous.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.url.params))
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        await client.vip.center_info(build=12345)
    assert seen == {"build": "12345"}


async def test_receive_privilege_source_derived_write():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://api.bilibili.com/x/vip/privilege/receive"
        form = parse_qs(request.content.decode(), keep_blank_values=True)
        assert form == {"type": ["1"], "csrf": ["csrf-token"]}
        return httpx.Response(200, json={"code": 0, "data": {"received": True}})

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.vip.receive_privilege(privilege_type_id=1)
        assert result == {"received": True}


async def test_receive_privilege_allows_missing_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
    ) as client:
        assert await client.vip.receive_privilege(privilege_type_id=1) is None


async def test_add_experience_source_derived_write():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://api.bilibili.com/x/vip/experience/add"
        form = parse_qs(request.content.decode(), keep_blank_values=True)
        assert form == {"csrf": ["csrf-token"]}
        return httpx.Response(200, json={"code": 0, "data": {"type": 1, "is_grant": True}})

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
    ) as client:
        data = await client.vip.add_experience()
        assert data.type == 1
        assert data.is_grant is True


@pytest.mark.parametrize("value", [0, 256, -1, "1"])
async def test_invalid_privilege_type_fails_before_network(value):
    async with AsyncBpiClient(cookie="bili_jct=csrf-token") as client:
        with pytest.raises(InvalidParameterError):
            await client.vip.receive_privilege(privilege_type_id=value)


async def test_writes_require_csrf_before_network():
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await client.vip.add_experience()


def test_vip_numeric_string_compatibility():
    vip = Vip.model_validate(
        {
            "type": "2",
            "status": "1",
            "due_date": "1813334400000",
            "role": "3",
            "mid": "1000001",
        }
    )
    assert vip.vip_type == 2
    assert vip.vip_status == 1
    assert vip.vip_due_date == 1_813_334_400_000
    assert vip.role == 3
    assert vip.mid == 1_000_001


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("vip/")]
    assert len(paths) == 4
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_vip_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "vip"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.vip.") and api["status"] == "implemented"
    }
    assert expected == {"center_info", "receive_privilege", "add_experience"}
    assert implemented == expected
    assert inspect.iscoroutinefunction(VipClient.center_info)
    assert inspect.iscoroutinefunction(VipClient.receive_privilege)
    assert inspect.iscoroutinefunction(VipClient.add_experience)
