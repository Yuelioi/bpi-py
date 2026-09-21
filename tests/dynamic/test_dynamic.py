from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import httpx
import pytest

from bpi import AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.dynamic import DynamicClient
from bpi.dynamic.models import DynamicContentItem, DynamicCreatePic, DynamicTopic

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
DYNAMIC_FIXTURES = FIXTURES / "dynamic/read"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("dynamic tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def _contract(path: str) -> dict[str, object]:
    return json.loads((DYNAMIC_FIXTURES / path / "contract.json").read_bytes())


def _response(path: str, filename: str) -> bytes:
    return (DYNAMIC_FIXTURES / path / "responses" / filename).read_bytes()


READ_CASES = [
    ("feed/all", "all", {}),
    ("feed/check-new", "check_new", {"update_baseline": "0"}),
    ("feed/nav", "nav_feed", {}),
    ("feed/banner", "feed_banner", {}),
    ("detail/detail", "detail", {"dynamic_id": "1099138163191840776"}),
    ("detail/reactions", "reactions", {"dynamic_id": "1099138163191840776"}),
    (
        "lottery-notice-read/lottery-notice",
        "lottery_notice",
        {"business_id": "969916293954142214"},
    ),
    ("detail/forwards", "forwards", {"dynamic_id": "1099138163191840776"}),
    ("detail/pics", "pics", {"dynamic_id": "1099138163191840776"}),
    (
        "detail/forward-item",
        "forward_item",
        {"dynamic_id": "1110902525317349376"},
    ),
    ("content/live-users", "live_users", {"size": 1}),
    ("content/up-users", "up_users", {}),
    ("content/recent-up", "recent_up", {}),
]


def _assert_query(request: httpx.Request, contract: dict[str, object]) -> None:
    expected = contract["request"]["query"]
    actual = dict(request.url.params)
    assert set(actual) == set(expected)
    for key, value in expected.items():
        if value == "${csrf}":
            assert actual[key] == "csrf-token"
        else:
            assert actual[key] == value


@pytest.mark.parametrize("fixture_path,method,kwargs", READ_CASES)
async def test_promoted_read_success_cases(
    fixture_path: str, method: str, kwargs: dict[str, object]
):
    contract = _contract(fixture_path)
    success_cases = [case for case in contract["cases"] if case["response"].get("error") is None]
    assert success_cases

    for case in success_cases:
        fixture = Path(case["response"]["fixture"]).name
        body = _response(fixture_path, fixture)

        def handler(request: httpx.Request, response_body: bytes = body) -> httpx.Response:
            assert request.method == "GET"
            assert str(request.url).split("?")[0] == contract["request"]["url"]
            _assert_query(request, contract)
            return httpx.Response(200, content=response_body)

        profile = case["profile"]
        cookie = "bili_jct=csrf-token" if method == "lottery_notice" else None
        if cookie is None and profile != "anonymous":
            cookie = "SESSDATA=fake"
        async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
            result = await getattr(client.dynamic, method)(**kwargs)
        assert result is not None


@pytest.mark.parametrize("fixture_path,method,kwargs", READ_CASES)
async def test_promoted_read_login_errors(
    fixture_path: str, method: str, kwargs: dict[str, object]
):
    contract = _contract(fixture_path)
    error_cases = [case for case in contract["cases"] if case["response"].get("error")]
    if not error_cases:
        return

    case = error_cases[0]
    body = _response(fixture_path, Path(case["response"]["fixture"]).name)

    def handler(request: httpx.Request) -> httpx.Response:
        _assert_query(request, contract)
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.dynamic, method)(**kwargs)


async def test_like_source_derived_json_request():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/dynamic/feed/dyn/thumb"
        assert dict(request.url.params) == {"csrf": "csrf-token"}
        assert json.loads(request.content) == {
            "dyn_id_str": "123",
            "up": 1,
            "spmid": "333.1369.0.0",
            "from_spmid": "333.999.0.0",
        }
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await client.dynamic.like(dyn_id_str=" 123 ", up=1) is None


async def test_delete_draft_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.vc.bilibili.com"
        assert request.url.path == "/dynamic_draft/v1/dynamic_draft/rm_draft"
        assert request.content == b"draft_id=draft-1&csrf=csrf-token"
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await client.dynamic.delete_draft(draft_id=" draft-1 ") is None


@pytest.mark.parametrize(
    "method,path",
    [("set_top", "/x/dynamic/feed/space/set_top"), ("remove_top", "/x/dynamic/feed/space/rm_top")],
)
async def test_top_actions_source_derived_json(method: str, path: str):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == path
        assert dict(request.url.params) == {"csrf": "csrf-token"}
        assert json.loads(request.content) == {"dyn_str": "456"}
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await getattr(client.dynamic, method)(dyn_str=" 456 ") is None


async def test_upload_pic_source_derived_multipart(tmp_path: Path):
    image = tmp_path / "cover.jpg"
    image.write_bytes(b"fake-jpeg-bytes")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/dynamic/feed/draw/upload_bfs"
        body = await request.aread()
        content_type = request.headers["content-type"]
        assert content_type.startswith("multipart/form-data; boundary=")
        for token in [
            b'name="file_up"; filename="cover.jpg"',
            b"Content-Type: image/jpeg",
            b"fake-jpeg-bytes",
            b'name="csrf"',
            b"csrf-token",
            b'name="category"',
            b"daily",
            b'name="biz"',
            b"new_dyn",
        ]:
            assert token in body
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "image_url": "https://example.invalid/a.jpg",
                    "image_width": 100,
                    "image_height": 80,
                    "img_size": 1.5,
                },
            },
        )

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.dynamic.upload_pic(file_path=image)
    assert result.image_width == 100


async def test_create_text_source_derived_multipart():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.vc.bilibili.com"
        assert request.url.path == "/dynamic_svr/v1/dynamic_svr/create"
        body = await request.aread()
        for token in [
            b'name="dynamic_id"',
            b"0",
            b'name="type"',
            b"4",
            b'name="rid"',
            b'name="content"',
            b"hello",
            b'name="csrf"',
            b'name="csrf_token"',
            b"csrf-token",
        ]:
            assert token in body
        return httpx.Response(
            200, json={"code": 0, "data": {"dynamic_id": 7, "dynamic_id_str": "7"}}
        )

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.dynamic.create_text(content=" hello ")
    assert result.dynamic_id == 7


async def test_create_complex_source_derived_json():
    content = DynamicContentItem(type_num=1, biz_id=None, raw_text="hello")
    pic = DynamicCreatePic(
        img_src="https://example.invalid/a.jpg", img_height=80, img_width=100, img_size=1.5
    )
    topic = DynamicTopic(id=9, name="topic")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/dynamic/feed/create/dyn"
        assert dict(request.url.params) == {"csrf": "csrf-token"}
        body = json.loads(request.content)["dyn_req"]
        assert body["scene"] == 2
        assert body["content"]["contents"][0] == {"type": 1, "biz_id": None, "raw_text": "hello"}
        assert body["pics"][0]["img_width"] == 100
        assert body["topic"]["id"] == 9
        assert body["meta"] == {"app_meta": {"from": "create.dynamic.web", "mobi_app": "web"}}
        return httpx.Response(
            200,
            json={"code": 0, "data": {"dyn_id": 8, "dyn_id_str": "8", "dyn_type": 2}},
        )

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.dynamic.create_complex(
            scene=2, contents=[content], pics=[pic], topic=topic
        )
    assert result.dyn_id == 8


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("all", {"features": "   "}),
        ("check_new", {"update_baseline": "   "}),
        ("nav_feed", {"offset": "   "}),
        ("detail", {"dynamic_id": "   "}),
        ("reactions", {"dynamic_id": "   "}),
        ("lottery_notice", {"business_id": "   "}),
        ("live_users", {"size": 0}),
        ("up_users", {"teenagers_mode": 1}),
        ("like", {"dyn_id_str": "1", "up": 3}),
        ("delete_draft", {"draft_id": "   "}),
        ("set_top", {"dyn_str": "   "}),
        ("remove_top", {"dyn_str": "   "}),
        ("upload_pic", {"file_path": "missing.jpg", "category": "   "}),
        ("create_text", {"content": "   "}),
        ("create_complex", {"scene": 3, "contents": []}),
        ("create_complex", {"scene": 1, "contents": []}),
    ],
)
async def test_invalid_arguments_fail_before_network(method: str, kwargs: dict[str, object]):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.dynamic, method)(**kwargs)


async def test_missing_upload_file_fails_before_csrf(tmp_path: Path):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.dynamic.upload_pic(file_path=tmp_path / "missing.jpg")


async def test_valid_write_requires_csrf_after_validation():
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await client.dynamic.like(dyn_id_str="1", up=1)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("dynamic/read/")]
    assert len(paths) == 50
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_dynamic_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "dynamic"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.dynamic.") and api["status"] == "implemented"
    }
    assert len(expected) == 20
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(DynamicClient, name, None)) for name in expected)
