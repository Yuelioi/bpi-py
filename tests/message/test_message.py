from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs
from uuid import UUID

import httpx
import pytest

from bpi import AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.message import MessageClient, MessageImage, SingleUnreadType

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
MESSAGE_FIXTURES = FIXTURES / "message/read"

WBI_BODY = {
    "code": 0,
    "data": {
        "wbi_img": {
            "img_url": "https://example.invalid/abcdefghijklmnopqrstuvwxyz123456.png",
            "sub_url": "https://example.invalid/ABCDEFGHIJKLMNOPQRSTUVWXYZ654321.png",
        }
    },
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("message tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def fixture(endpoint: str, name: str) -> bytes:
    return (MESSAGE_FIXTURES / endpoint / name).read_bytes()


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
@pytest.mark.parametrize(
    "endpoint,method_name",
    [
        ("unread-count", "unread_count"),
        ("reply-feed", "reply_feed"),
        ("single-unread", "single_unread"),
    ],
)
async def test_promoted_read_contracts(profile, endpoint, method_name):
    contract = json.loads(fixture(endpoint, "contract.json"))
    response_name = (
        "anonymous.requires_login.json" if profile == "anonymous" else "authenticated.success.json"
    )
    body = fixture(endpoint, f"responses/{response_name}")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        call = getattr(client.message, method_name)
        if profile == "anonymous":
            with pytest.raises(AuthenticationError):
                await call()
        else:
            data = await call()
            if method_name == "unread_count":
                assert data.sys_msg == 1
                assert data.danmu == 0
            elif method_name == "reply_feed":
                assert data.items[0].item.reply_type == "video"
            else:
                assert data.follow_unread == 0


async def test_reply_feed_cursor_and_single_unread_flags():
    seen: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(dict(request.url.params))
        if request.url.path == "/x/msgfeed/reply":
            return httpx.Response(
                200, content=fixture("reply-feed", "responses/authenticated.success.json")
            )
        return httpx.Response(
            200, content=fixture("single-unread", "responses/authenticated.success.json")
        )

    async with AsyncBpiClient(
        cookie="SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        await client.message.reply_feed(
            start_id=1001, start_time=1_700_000_000, web_location="333.401"
        )
        await client.message.single_unread(
            unread_type=SingleUnreadType.BLOCKED,
            show_unfollow_list=True,
        )

    assert seen[0] == {
        "build": "0",
        "mobi_app": "web",
        "platform": "web",
        "web_location": "333.401",
        "id": "1001",
        "reply_time": "1700000000",
    }
    assert seen[1]["unread_type"] == "3"
    assert seen[1]["show_unfollow_list"] == "1"
    assert seen[1]["show_dustbin"] == "1"


async def test_send_text_source_derived_write():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.bilibili.com" and request.url.path == "/x/web-interface/nav":
            return httpx.Response(200, json=WBI_BODY)

        assert request.method == "POST"
        assert request.url.host == "api.vc.bilibili.com"
        assert request.url.path == "/web_im/v1/web_im/send_msg"
        query = dict(request.url.params)
        assert query["w_sender_uid"] == "1000001"
        assert query["w_receiver_id"] == "2000002"
        UUID(query["w_dev_id"])
        assert "wts" in query and "w_rid" in query

        form = parse_qs(request.content.decode(), keep_blank_values=True)
        captured["form"] = form
        assert form["msg[sender_uid]"] == ["1000001"]
        assert form["msg[receiver_id]"] == ["2000002"]
        assert form["msg[receiver_type]"] == ["1"]
        assert form["msg[msg_type]"] == ["1"]
        assert form["msg[timestamp]"] == ["1700000000"]
        assert form["csrf"] == ["csrf-token"]
        assert form["csrf_token"] == ["csrf-token"]
        assert json.loads(form["msg[content]"][0]) == {"content": "hello"}
        assert form["msg[dev_id]"][0] == query["w_dev_id"]
        return httpx.Response(200, json={"code": 0, "data": {"msg_key": 123}})

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=csrf-token; DedeUserID=1000001",
        transport=httpx.MockTransport(handler),
        clock=lambda: 1_700_000_000.0,
    ) as client:
        data = await client.message.send(receiver_id=2_000_002, message="hello")
        assert data.msg_key == 123
    assert captured


def test_send_image_serializes_rust_shape():
    image = MessageImage(
        url="https://example.invalid/image.jpg",
        height=100,
        width=200,
        imageType="jpg",
        original=1,
        size=12.5,
    )
    assert json.loads(image.model_dump_json(by_alias=True))["imageType"] == "jpg"


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("unread_count", {"mobi_app": " "}),
        ("reply_feed", {"start_id": 0}),
        ("reply_feed", {"start_time": 0}),
        ("single_unread", {"unread_type": -1}),
    ],
)
async def test_invalid_read_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.message, method)(**kwargs)


async def test_send_requires_csrf_and_sender_uid():
    async with AsyncBpiClient(cookie="SESSDATA=fake; DedeUserID=1") as client:
        with pytest.raises(AuthenticationError):
            await client.message.send(receiver_id=2, message="x")

    async with AsyncBpiClient(cookie="SESSDATA=fake; bili_jct=csrf-token") as client:
        with pytest.raises(AuthenticationError):
            await client.message.send(receiver_id=2, message="x")


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("message/")]
    assert len(paths) == 9
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_message_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "message"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.message.") and api["status"] == "implemented"
    }
    assert expected == {"unread_count", "reply_feed", "single_unread", "send"}
    assert implemented == expected
    assert inspect.iscoroutinefunction(MessageClient.unread_count)
    assert inspect.iscoroutinefunction(MessageClient.reply_feed)
    assert inspect.iscoroutinefunction(MessageClient.single_unread)
    assert inspect.iscoroutinefunction(MessageClient.send)
