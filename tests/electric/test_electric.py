from __future__ import annotations

import hashlib
import inspect
import json
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.electric import ElectricClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
ELECTRIC_FIXTURES = FIXTURES / "electric/read"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("electric tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


READ_CASES = [
    ("month-up-list", "month_up_list", {"up_mid": 53456}, "success.json", None),
    (
        "video-show",
        "video_show",
        {"mid": 53456, "bvid": "BV1Dh411S7sS"},
        "success.json",
        None,
    ),
    (
        "recharge-list",
        "recharge_list",
        {"page": 1, "page_size": 10},
        "authenticated.success.json",
        "SESSDATA=fake",
    ),
    (
        "rank-recent",
        "rank_recent",
        {"pn": 1, "ps": 10},
        "normal.success.json",
        "SESSDATA=fake",
    ),
    (
        "charge-record",
        "charge_record",
        {"page": 1, "charge_type": 1},
        "authenticated.success.json",
        "SESSDATA=fake",
    ),
    (
        "upower-item-detail",
        "upower_item_detail",
        {"up_mid": 1265680561},
        "success.json",
        None,
    ),
    (
        "charge-follow-info",
        "charge_follow_info",
        {"up_mid": 1265680561},
        "authenticated.success.json",
        "SESSDATA=fake",
    ),
    (
        "upower-member-rank",
        "upower_member_rank",
        {"up_mid": 1265680561, "pn": 1, "ps": 10},
        "anonymous.success.json",
        None,
    ),
    (
        "remark-list",
        "remark_list",
        {"pn": 1, "ps": 10},
        "authenticated.success.json",
        "SESSDATA=fake",
    ),
    (
        "remark-detail",
        "remark_detail",
        {"id": 1},
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
    fixture_dir = ELECTRIC_FIXTURES / endpoint
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / "responses" / response_file).read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        result = await getattr(client.electric, method)(**kwargs)

    assert result is not None


@pytest.mark.parametrize(
    "endpoint,method,kwargs,response_file",
    [
        (
            "recharge-list",
            "recharge_list",
            {"page": 1, "page_size": 10},
            "anonymous.requires_login.json",
        ),
        ("rank-recent", "rank_recent", {"pn": 1, "ps": 10}, "anonymous.requires_login.json"),
        (
            "charge-record",
            "charge_record",
            {"page": 1, "charge_type": 1},
            "anonymous.requires_login.json",
        ),
        (
            "charge-follow-info",
            "charge_follow_info",
            {"up_mid": 1265680561},
            "anonymous.requires_login.json",
        ),
        ("remark-list", "remark_list", {"pn": 1, "ps": 10}, "anonymous.requires_login.json"),
        ("remark-detail", "remark_detail", {"id": 1}, "anonymous.requires_login.json"),
    ],
)
async def test_private_read_contracts_classify_login_errors(
    endpoint, method, kwargs, response_file
):
    body = (ELECTRIC_FIXTURES / endpoint / "responses" / response_file).read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.electric, method)(**kwargs)


async def test_date_filters_and_optional_rank_are_serialized():
    body = (ELECTRIC_FIXTURES / "recharge-list/responses/authenticated.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == {
            "customerId": "10026",
            "currentPage": "2",
            "pageSize": "20",
            "beginTime": "2026-08-01",
            "endTime": "2026-08-31",
        }
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        await client.electric.recharge_list(
            page=2,
            page_size=20,
            begin_time=date(2026, 8, 1),
            end_time=date(2026, 8, 31),
        )


async def test_bcoin_quick_pay_source_derived_form():
    expected = {
        "bp_num": ["20"],
        "is_bp_remains_prior": ["true"],
        "up_mid": ["42"],
        "otype": ["up"],
        "oid": ["42"],
        "csrf": ["csrf-token"],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/ugcpay/web/v2/trade/elec/pay/quick"
        assert parse_qs(request.content.decode(), keep_blank_values=True) == expected
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "mid": 1,
                    "up_mid": 42,
                    "order_no": "order-1",
                    "bp_num": "20",
                    "exp": 2,
                    "status": 4,
                    "msg": "",
                },
            },
        )

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.electric.bcoin_quick_pay(
            bp_num=20,
            is_bp_remains_prior=True,
            up_mid=42,
            otype="up",
            oid=42,
        )
    assert result.status == 4


async def test_send_message_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/ugcpay/trade/elec/message"
        assert parse_qs(request.content.decode(), keep_blank_values=True) == {
            "order_id": ["order-1"],
            "message": ["hello"],
            "csrf": ["csrf-token"],
        }
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.electric.send_message(order_id=" order-1 ", message=" hello ")
    assert result is None


async def test_reply_remark_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "member.bilibili.com"
        assert request.url.path == "/x/web/elec/remark/reply"
        assert parse_qs(request.content.decode(), keep_blank_values=True) == {
            "id": ["7"],
            "msg": ["thanks"],
            "csrf": ["csrf-token"],
        }
        return httpx.Response(200, json={"code": 0, "data": 7})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await client.electric.reply_remark(id=7, msg=" thanks ") == 7


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("month_up_list", {"up_mid": 0}),
        ("video_show", {"mid": 0}),
        ("recharge_list", {"page": 0, "page_size": 10}),
        ("rank_recent", {"pn": 0}),
        ("charge_record", {"page": 1, "charge_type": -1}),
        ("upower_item_detail", {"up_mid": 0}),
        ("upower_member_rank", {"up_mid": 1, "pn": 1, "ps": 0}),
        ("remark_detail", {"id": 0}),
        (
            "bcoin_quick_pay",
            {"bp_num": 1, "is_bp_remains_prior": True, "up_mid": 1, "otype": "up", "oid": 1},
        ),
        (
            "bcoin_quick_pay",
            {"bp_num": 20, "is_bp_remains_prior": 1, "up_mid": 1, "otype": "up", "oid": 1},
        ),
        (
            "bcoin_quick_pay",
            {"bp_num": 20, "is_bp_remains_prior": True, "up_mid": 1, "otype": "bad", "oid": 1},
        ),
        ("send_message", {"order_id": " ", "message": "x"}),
        ("reply_remark", {"id": 0, "msg": "x"}),
        ("reply_remark", {"id": 1, "msg": " "}),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=csrf-token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.electric, method)(**kwargs)


@pytest.mark.parametrize(
    "method,kwargs",
    [
        (
            "bcoin_quick_pay",
            {"bp_num": 20, "is_bp_remains_prior": True, "up_mid": 1, "otype": "up", "oid": 1},
        ),
        ("send_message", {"order_id": "order", "message": "message"}),
        ("reply_remark", {"id": 1, "msg": "reply"}),
    ],
)
async def test_writes_require_csrf_after_validation(method, kwargs):
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.electric, method)(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("electric/")]
    assert len(paths) == 28
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_electric_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "electric"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.electric.") and api["status"] == "implemented"
    }
    assert len(expected) == 13
    assert implemented == expected
    assert all(
        inspect.iscoroutinefunction(getattr(ElectricClient, name, None)) for name in expected
    )
