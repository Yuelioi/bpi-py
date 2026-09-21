from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import ApiError, AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.note import NoteClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
NOTE_FIXTURES = FIXTURES / "note/read"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("note tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


SUCCESS_CASES = [
    ("is-forbid", "is_forbid", {"aid": 338677252}, "success.json", None),
    (
        "private-info",
        "private_info",
        {"aid": 676931260, "note_id": 83577722856540160},
        "vip.success.json",
        "SESSDATA=fake",
    ),
    ("public-info", "public_info", {"cvid": 15160286}, "success.json", None),
    (
        "archive-list",
        "archive_list",
        {"aid": 676931260},
        "authenticated.success.json",
        "SESSDATA=fake",
    ),
    (
        "user-private-list",
        "user_private_list",
        {},
        "authenticated.success.json",
        "SESSDATA=fake",
    ),
    (
        "public-archive-list",
        "public_archive_list",
        {"aid": 338677252},
        "closed.success.json",
        None,
    ),
    (
        "user-public-list",
        "user_public_list",
        {},
        "authenticated.success.json",
        "SESSDATA=fake",
    ),
]


@pytest.mark.parametrize(
    "endpoint,method,kwargs,response_file,cookie",
    SUCCESS_CASES,
    ids=[case[0] for case in SUCCESS_CASES],
)
async def test_promoted_read_contracts(endpoint, method, kwargs, response_file, cookie):
    fixture_dir = NOTE_FIXTURES / endpoint
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / "responses" / response_file).read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        result = await getattr(client.note, method)(**kwargs)

    assert result is not None


@pytest.mark.parametrize(
    "endpoint,method,kwargs,response_file,code",
    [
        (
            "private-info",
            "private_info",
            {"aid": 676931260, "note_id": 83577722856540160},
            "anonymous.requires_login.json",
            -101,
        ),
        (
            "private-info",
            "private_info",
            {"aid": 676931260, "note_id": 83577722856540160},
            "normal.not_owner.json",
            79511,
        ),
        (
            "archive-list",
            "archive_list",
            {"aid": 676931260},
            "anonymous.requires_login.json",
            -101,
        ),
        (
            "user-private-list",
            "user_private_list",
            {},
            "anonymous.requires_login.json",
            -101,
        ),
    ],
)
async def test_promoted_error_contracts(endpoint, method, kwargs, response_file, code):
    body = (NOTE_FIXTURES / endpoint / "responses" / response_file).read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ApiError) as exc_info:
            await getattr(client.note, method)(**kwargs)
    assert exc_info.value.code == code


async def test_custom_pagination_is_serialized():
    body = (NOTE_FIXTURES / "user-private-list/responses/authenticated.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == {"pn": "2", "ps": "20"}
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        await client.note.user_private_list(page=2, page_size=20)


async def test_add_source_derived_form():
    expected = {
        "oid": ["170001"],
        "oid_type": ["0"],
        "title": ["title"],
        "summary": ["summary"],
        "content": ['[{"insert":"hello"}]'],
        "cls": ["1"],
        "from": ["save"],
        "platform": ["web"],
        "csrf": ["csrf-token"],
        "tags": ["tag-a"],
        "note_id": ["123"],
        "publish": ["1"],
        "auto_comment": ["0"],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/note/add"
        assert parse_qs(request.content.decode(), keep_blank_values=True) == expected
        return httpx.Response(200, json={"code": 0, "data": {"note_id": "123"}})

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.note.add(
            aid=170001,
            title="title",
            summary="summary",
            content="hello",
            tags="tag-a",
            note_id="123",
            publish=True,
            auto_comment=False,
        )
    assert result.note_id == "123"


@pytest.mark.parametrize("note_id", [None, "123"])
async def test_delete_source_derived_form(note_id):
    def handler(request: httpx.Request) -> httpx.Response:
        form = parse_qs(request.content.decode(), keep_blank_values=True)
        assert form["oid"] == ["170001"]
        assert form["csrf"] == ["csrf-token"]
        assert form.get("note_id") == (["123"] if note_id else None)
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await client.note.delete(aid=170001, note_id=note_id) is None


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("is_forbid", {"aid": 0}),
        ("private_info", {"aid": 1, "note_id": 0}),
        ("public_info", {"cvid": 0}),
        ("user_private_list", {"page": 0}),
        ("public_archive_list", {"aid": 1, "page_size": 0}),
        ("add", {"aid": 1, "title": " ", "summary": "s", "content": "c"}),
        ("add", {"aid": 1, "title": "t", "summary": "s", "content": "c", "publish": 1}),
        ("delete", {"aid": 1, "note_id": " "}),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=csrf-token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.note, method)(**kwargs)


async def test_write_requires_csrf_after_validation():
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await client.note.delete(aid=170001)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("note/")]
    assert len(paths) == 19
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_note_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "note"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.note.") and api["status"] == "implemented"
    }
    assert len(expected) == 9
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(NoteClient, name, None)) for name in expected)
