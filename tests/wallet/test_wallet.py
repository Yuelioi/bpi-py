from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import httpx
import pytest

from bpi import AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.wallet import WalletClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
WALLET_FIXTURES = FIXTURES / "wallet/read/info"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("wallet tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize("profile", ["normal", "vip"])
async def test_wallet_info_promoted_contract(profile):
    contract = json.loads((WALLET_FIXTURES / "contract.json").read_bytes())
    body = (WALLET_FIXTURES / "responses/authenticated.success.json").read_bytes()
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.method == "POST"
        assert str(request.url) == contract["request"]["url"]
        assert request.headers["content-type"].startswith("application/json")
        expected = dict(contract["request"]["body"])
        expected["csrf"] = "token"
        assert json.loads(request.content) == expected
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=token",
        transport=httpx.MockTransport(handler),
        clock=lambda: 1700000000.0,
    ) as client:
        wallet = await client.wallet.info()
        assert wallet.mid == 1000001
        assert wallet.need_show_class_balance == 1

    assert len(calls) == 1


async def test_wallet_info_custom_body():
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "mid": 1,
                    "totalBp": 0.0,
                    "defaultBp": 0.0,
                    "iosBp": 0.0,
                    "couponBalance": 0.0,
                    "availableBp": 0.0,
                    "unavailableBp": 0.0,
                    "unavailableReason": "",
                    "tip": "",
                    "needShowClassBalance": 1,
                },
            },
        )

    async with AsyncBpiClient(
        cookie="bili_jct=token", transport=httpx.MockTransport(handler)
    ) as client:
        await client.wallet.info(
            timestamp_ms=1700000000123,
            platform_type=4,
            trace_id=1700000000456,
            version=" 2.0 ",
        )

    assert seen == {
        "csrf": "token",
        "platformType": 4,
        "timestamp": 1700000000123,
        "traceId": 1700000000456,
        "version": "2.0",
    }


async def test_wallet_requires_csrf_before_network():
    async with AsyncBpiClient() as client:
        with pytest.raises(AuthenticationError):
            await client.wallet.info()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"platform_type": 0},
        {"timestamp_ms": "1700000000000"},
        {"trace_id": 0},
        {"version": " "},
    ],
)
async def test_invalid_arguments_fail_before_network(kwargs):
    async with AsyncBpiClient(cookie="bili_jct=token") as client:
        with pytest.raises(InvalidParameterError):
            await client.wallet.info(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("wallet/")]
    assert len(paths) == 2
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_wallet_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "wallet"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.wallet.") and api["status"] == "implemented"
    }
    assert expected == {"info"}
    assert implemented == expected
    assert inspect.iscoroutinefunction(WalletClient.info)
