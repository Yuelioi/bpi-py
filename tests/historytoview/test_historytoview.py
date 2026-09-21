from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest
from pydantic import ValidationError

from bpi import (
    ApiError,
    AsyncBpiClient,
    AuthenticationError,
    InvalidParameterError,
    ResponseDecodeError,
)
from bpi.historytoview import HistoryListData, HistoryToViewClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
HTV_FIXTURES = FIXTURES / "historytoview"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("HistoryToView tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


READS = [
    ("history-list", "history_list", {"page_size": 5}),
    ("history-shadow", "history_shadow", {}),
    ("toview-list", "toview_list", {}),
]


@pytest.mark.parametrize("directory,method,kwargs", READS, ids=[case[0] for case in READS])
async def test_promoted_read_contracts(directory, method, kwargs):
    contract = json.loads((HTV_FIXTURES / directory / "contract.json").read_bytes())
    calls = []

    def handler(request):
        calls.append(request)
        expected = contract["request"]
        assert request.method == expected["method"]
        assert str(request.url).split("?")[0] == expected["url"]
        assert dict(request.url.params) == expected["query"]
        authenticated = "SESSDATA=fake" in request.headers.get("cookie", "")
        case = contract["cases"][1 if authenticated else 0]
        body = (HTV_FIXTURES / directory / case["response"]["fixture"]).read_bytes()
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.historytoview, method)(**kwargs)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        result = await getattr(client.historytoview, method)(**kwargs)
        assert result is not None

    assert len(calls) == 2


def test_history_fixture_preserves_signed_integer_fields():
    payload = json.loads(
        (HTV_FIXTURES / "history-list/responses/authenticated.success.json").read_bytes()
    )["data"]
    model = HistoryListData.model_validate(payload)
    assert model.list[0].total == -1
    payload["list"][0]["view_at"] = "1"
    with pytest.raises(ValidationError):
        HistoryListData.model_validate(payload)


WRITES = [
    (
        "delete_history",
        {"kid": "archive_1"},
        "/x/v2/history/delete",
        {"kid": "archive_1", "csrf": "token"},
    ),
    (
        "clear_history",
        {},
        "/x/v2/history/clear",
        {"csrf": "token"},
    ),
    (
        "set_history_shadow",
        {"switch": True},
        "/x/v2/history/shadow/set",
        {"switch": "true", "csrf": "token"},
    ),
    (
        "add_toview",
        {"aid": 170001},
        "/x/v2/history/toview/add",
        {"csrf": "token", "aid": "170001"},
    ),
    (
        "delete_toview",
        {"viewed": True},
        "/x/v2/history/toview/del",
        {"csrf": "token", "viewed": "true"},
    ),
    (
        "clear_toview",
        {},
        "/x/v2/history/toview/clear",
        {"csrf": "token"},
    ),
]


@pytest.mark.parametrize("case", WRITES, ids=[case[0] for case in WRITES])
@pytest.mark.parametrize("response_kind", ["success", "error"])
async def test_write_protocol_is_source_derived(case, response_kind):
    name, kwargs, path, expected_form = case
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "POST"
        assert request.url.host == "api.bilibili.com"
        assert request.url.path == path
        assert dict(request.url.params) == {}
        actual = dict(parse_qsl(request.content.decode(), keep_blank_values=True))
        assert actual == expected_form
        if response_kind == "error":
            return httpx.Response(200, json={"code": -403, "message": "denied"})
        return httpx.Response(200, json={"code": 0, "message": "OK"})

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=token",
        transport=httpx.MockTransport(handler),
    ) as client:
        method = getattr(client.historytoview, name)
        if response_kind == "error":
            with pytest.raises(ApiError) as error:
                await method(**kwargs)
            assert error.value.code == -403
        else:
            assert await method(**kwargs) is None
    assert len(calls) == 1


@pytest.mark.parametrize("case", WRITES, ids=[case[0] for case in WRITES])
async def test_writes_require_csrf_before_network(case):
    async with AsyncBpiClient() as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.historytoview, case[0])(**case[1])


@pytest.mark.parametrize(
    "name,kwargs",
    [
        ("history_list", {"max_id": True}),
        ("history_list", {"business": " "}),
        ("history_list", {"list_type": " "}),
        ("history_list", {"page_size": 0}),
        ("delete_history", {"kid": " "}),
        ("set_history_shadow", {"switch": 1}),
        ("add_toview", {}),
        ("add_toview", {"aid": 0}),
        ("add_toview", {"bvid": " "}),
        ("delete_toview", {}),
        ("delete_toview", {"aid": 0}),
        ("delete_toview", {"viewed": 1}),
    ],
)
async def test_invalid_arguments_fail_before_network(name, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.historytoview, name)(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("historytoview/")]
    assert len(paths) == 9
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


async def test_history_shadow_rejects_string_boolean():
    def handler(request):
        return httpx.Response(200, json={"code": 0, "data": "false"})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ResponseDecodeError):
            await client.historytoview.history_shadow()


def test_complete_historytoview_module_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {
        method["name"] for method in inventory["methods"] if method["domain"] == "historytoview"
    }
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.historytoview.")
        and api["status"] == "implemented"
    }
    assert len(expected) == 9
    assert implemented == expected
    assert all(
        inspect.iscoroutinefunction(getattr(HistoryToViewClient, name, None)) for name in expected
    )
