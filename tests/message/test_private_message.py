from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import AsyncBpiClient
from bpi.errors import (
    AuthenticationError,
    InvalidParameterError,
    MissingDataError,
    ResponseDecodeError,
)
from bpi.message import SessionListType

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
COOKIE = "DedeUserID=1000001; SESSDATA=fixture; bili_jct=fixture-csrf; buvid3=fixture-device"
WBI = {
    "code": -101,
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
        raise AssertionError("private-message tests must be offline")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize(
    "endpoint,method",
    [
        ("sessions", "sessions"),
        ("session-messages", "session_messages"),
    ],
)
@pytest.mark.parametrize("case_name", ["anonymous", "normal", "vip", "vip_empty"])
async def test_private_read_rust_contract(endpoint, method, case_name):
    folder = FIXTURES / "message/private-read" / endpoint
    contract = json.loads((folder / "contract.json").read_bytes())
    case = next(c for c in contract["cases"] if c["name"] == case_name)
    body = (folder / case["response"]["fixture"]).read_bytes()
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == contract["request"]["method"]
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    kwargs = {"talker_id": 1000001} if method == "session_messages" else {}
    async with AsyncBpiClient(
        cookie=None if case_name == "anonymous" else COOKIE,
        transport=httpx.MockTransport(handler),
    ) as client:
        if case["response"]["api_code"] != 0:
            with pytest.raises(AuthenticationError):
                await getattr(client.message, method)(**kwargs)
        else:
            result = await getattr(client.message, method)(**kwargs)
            items = result.session_list if method == "sessions" else result.messages
            if case_name == "vip_empty":
                assert items is None
            else:
                assert items
                if method == "session_messages":
                    assert any(m.new_face_version is None for m in items)
    assert len(calls) == 1


async def test_private_read_cursors_and_categories():
    seen = []

    def handler(request):
        seen.append(dict(request.url.params))
        folder = "sessions" if request.url.path.endswith("get_sessions") else "session-messages"
        body = (
            FIXTURES / "message/private-read" / folder / "responses/vip.empty.json"
        ).read_bytes()
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        await client.message.sessions(
            session_type=SessionListType.UNFOLLOWED,
            size=2,
            begin_ts=1700000000000000,
            end_ts=1700000001000000,
        )
        await client.message.session_messages(talker_id=1000001, begin_seqno=10, end_seqno=20)
    assert seen[0]["session_type"] == "2"
    assert seen[0]["begin_ts"] == "1700000000000000"
    assert seen[0]["end_ts"] == "1700000001000000"
    assert seen[1]["begin_seqno"] == "10"
    assert seen[1]["end_seqno"] == "20"


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("sessions", {"size": 0}),
        ("sessions", {"size": 101}),
        ("sessions", {"session_type": 3}),
        ("sessions", {"session_type": True}),
        ("sessions", {"begin_ts": 0}),
        ("sessions", {"end_ts": 0}),
        ("sessions", {"begin_ts": 2**64}),
        ("session_messages", {"talker_id": 0}),
        ("session_messages", {"talker_id": 1, "begin_seqno": 0}),
        ("session_messages", {"talker_id": 1, "end_seqno": 0}),
        ("session_messages", {"talker_id": 1, "size": True}),
        ("session_messages", {"talker_id": 2**64}),
        ("send", {"receiver_id": 1, "message": " \n "}),
        ("send", {"receiver_id": 1, "message": "中" * 663}),
        ("send", {"receiver_id": 1, "message": '"' * 1000}),
        ("send", {"receiver_id": 1, "message": "\ud800"}),
    ],
)
async def test_invalid_arguments_do_not_make_requests(method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.message, method)(**kwargs)


@pytest.mark.parametrize("message", ["<redacted>", ' 收到\n<&>\u2028\u2029\\" ', "a" * 1986])
async def test_send_rust_contract_and_text_encoding(message):
    folder = FIXTURES / "message/private-write/send"
    contract = json.loads((folder / "contract.json").read_bytes())
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path == "/x/web-interface/nav":
            return httpx.Response(200, json=WBI)
        assert request.method == "POST"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        form = {k: values[0] for k, values in parse_qs(request.content.decode()).items()}
        expected = dict(contract["request"]["form"])
        expected.update(
            {
                "csrf": "fixture-csrf",
                "csrf_token": "fixture-csrf",
                "msg[dev_id]": form["msg[dev_id]"],
                "msg[timestamp]": "1700000000",
                "msg[content]": json.dumps(
                    {"content": message}, ensure_ascii=False, separators=(",", ":")
                ),
            }
        )
        assert form == expected
        query = dict(request.url.params)
        assert query["w_dev_id"] == form["msg[dev_id]"]
        assert query["w_sender_uid"] == "1000001"
        assert query["w_receiver_id"] == "1000001"
        assert len(query["w_rid"]) == 32 and query["wts"] == "1700000000"
        return httpx.Response(
            200, content=(folder / "responses/synthetic.success.json").read_bytes()
        )

    async with AsyncBpiClient(
        cookie=COOKIE,
        clock=lambda: 1700000000.0,
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.message.send(receiver_id=1000001, message=message)
    assert result.msg_key == 1000001
    assert len(calls) == 2


@pytest.mark.parametrize(
    "body,error",
    [
        (b'{"code":-101,"data":{"messages":"private-marker"}}', AuthenticationError),
        (b'{"code":0,"data":{"messages":"private-marker"}}', ResponseDecodeError),
        (b'{"code":0,"data":{}}', ResponseDecodeError),
        (b'{"code":0,"data":null}', MissingDataError),
    ],
)
async def test_error_semantics_and_private_body(body, error):
    async with AsyncBpiClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    ) as client:
        with pytest.raises(error) as caught:
            await client.message.session_messages(talker_id=1)
        assert "private-marker" not in str(caught.value)
        if isinstance(caught.value, ResponseDecodeError):
            assert caught.value.response_body == body


async def test_uncertain_send_does_not_retry():
    posts = []

    def handler(request):
        if request.url.path == "/x/web-interface/nav":
            return httpx.Response(200, json=WBI)
        posts.append(request)
        raise httpx.ReadTimeout("uncertain delivery")

    from bpi.errors import TransportError

    async with AsyncBpiClient(cookie=COOKIE, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(TransportError):
            await client.message.send(receiver_id=1000001, message="x")
    assert len(posts) == 1


def test_committed_provenance_and_exact_fixture_hashes():
    manifest = json.loads((ROOT / "migration/private-message.json").read_bytes())
    assert manifest["source_state"] == "committed_source"
    assert len(manifest["source_commit"]) == 40
    hashes = {
        path: digest
        for path, digest in manifest["sha256"].items()
        if path.startswith("tests/contracts/")
    }
    assert len(hashes) == 13
    for source_path, digest in hashes.items():
        relative = source_path.removeprefix("tests/contracts/")
        assert hashlib.sha256((FIXTURES / relative).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("omit", [False, True])
async def test_sessions_without_last_message(omit):
    path = FIXTURES / "message/private-read/sessions/responses/vip.no-last-message.json"
    body = json.loads(path.read_bytes())
    if omit:
        del body["data"]["session_list"][0]["last_msg"]
    async with AsyncBpiClient(
        cookie=COOKIE,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body)),
    ) as client:
        result = await client.message.sessions(session_type=SessionListType.USER_AND_SYSTEM)
    assert result.session_list is not None
    assert result.session_list[0].last_msg is None
