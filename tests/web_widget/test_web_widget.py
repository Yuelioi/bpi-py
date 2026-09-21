from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import httpx
import pytest

from bpi import AsyncBpiClient, InvalidParameterError
from bpi.web_widget import WebWidgetClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
WEB_WIDGET_FIXTURES = FIXTURES / "web_widget"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("web_widget tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_region_banner_promoted_contract(profile):
    base = WEB_WIDGET_FIXTURES / "region-banner"
    contract = json.loads((base / "contract.json").read_bytes())
    body = (base / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        data = await client.web_widget.region_banner(region_id=1005)
        assert data.region_banner_list
        assert data.region_banner_list[0].rid == 1005


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_header_page_promoted_contract(profile):
    base = WEB_WIDGET_FIXTURES / "header-page"
    contract = json.loads((base / "contract.json").read_bytes())
    body = (base / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        data = await client.web_widget.header_page()
        assert data.is_split_layer == 1
        assert data.split_layer_obj is not None
        assert data.split_layer_obj.layers


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
async def test_online_promoted_contract(profile):
    base = WEB_WIDGET_FIXTURES / "online"
    contract = json.loads((base / "contract.json").read_bytes())
    body = (base / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == contract["request"]["url"]
        assert not request.url.params
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        data = await client.web_widget.online()
        assert data.region_count
        assert data.region_count["1"] > 0


async def test_header_page_custom_resource_id():
    seen: dict[str, str] = {}
    body = (WEB_WIDGET_FIXTURES / "header-page/responses/anonymous.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.url.params))
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        await client.web_widget.header_page(resource_id=143)
    assert seen == {"resource_id": "143"}


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("region_banner", {"region_id": 0}),
        ("region_banner", {"region_id": "1005"}),
        ("header_page", {"resource_id": 0}),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.web_widget, method)(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("web_widget/")]
    assert len(paths) == 12
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_web_widget_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {
        method["name"] for method in inventory["methods"] if method["domain"] == "web_widget"
    }
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.web_widget.") and api["status"] == "implemented"
    }
    assert expected == {"region_banner", "header_page", "online"}
    assert implemented == expected
    assert inspect.iscoroutinefunction(WebWidgetClient.region_banner)
    assert inspect.iscoroutinefunction(WebWidgetClient.header_page)
    assert inspect.iscoroutinefunction(WebWidgetClient.online)
