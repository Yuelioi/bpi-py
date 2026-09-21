from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.comment import CommentClient, CommentSort, CommentType, ReportReason

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
COMMENT_FIXTURES = FIXTURES / "comment/read"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("comment tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


READ_CASES = [
    (
        "list",
        "list",
        {
            "comment_type": 1,
            "oid": 23199,
            "page": 1,
            "page_size": 5,
            "sort": CommentSort.TIME,
            "nohot": False,
        },
    ),
    (
        "replies",
        "replies",
        {"comment_type": 1, "oid": 23199, "root": 2554491176, "page": 1, "page_size": 5},
    ),
    (
        "hot",
        "hot",
        {"comment_type": 1, "oid": 23199, "root": 2554491176, "page": 1, "page_size": 5},
    ),
    ("count", "count", {"comment_type": 1, "oid": 23199}),
]


@pytest.mark.parametrize("profile", ["anonymous", "normal", "vip"])
@pytest.mark.parametrize("endpoint,method,kwargs", READ_CASES, ids=[case[0] for case in READ_CASES])
async def test_promoted_read_contracts(profile, endpoint, method, kwargs):
    fixture_dir = COMMENT_FIXTURES / endpoint
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / f"responses/{profile}.success.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        assert dict(request.url.params) == contract["request"]["query"]
        return httpx.Response(200, content=body)

    cookie = None if profile == "anonymous" else "SESSDATA=fake"
    async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
        result = await getattr(client.comment, method)(**kwargs)

    if endpoint == "hot":
        assert result is None
    elif endpoint == "count":
        assert result.count == 10
    else:
        assert result.page is not None


async def test_add_source_derived_form():
    expected = {
        "type": ["1"],
        "oid": ["23199"],
        "message": ["hello"],
        "plat": ["1"],
        "csrf": ["csrf-token"],
        "root": ["2554491176"],
        "parent": ["2554491177"],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/v2/reply/add"
        assert parse_qs(request.content.decode(), keep_blank_values=True) == expected
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "rpid": 9,
                    "rpid_str": "9",
                    "root": 2554491176,
                    "root_str": "2554491176",
                    "parent": 2554491177,
                    "parent_str": "2554491177",
                    "dialog": 2554491176,
                    "dialog_str": "2554491176",
                    "success_toast": None,
                },
            },
        )

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.comment.add(
            comment_type=CommentType.VIDEO,
            oid=23199,
            message="  hello  ",
            root=2554491176,
            parent=2554491177,
        )
    assert result.rpid == 9


@pytest.mark.parametrize(
    "method,path,kwargs,extra",
    [
        ("like", "/x/v2/reply/action", {"action": 1}, {"action": ["1"]}),
        ("dislike", "/x/v2/reply/hate", {"action": 0}, {"action": ["0"]}),
        ("top", "/x/v2/reply/top", {"action": 1}, {"action": ["1"]}),
        ("delete", "/x/v2/reply/del", {}, {}),
        (
            "report",
            "/x/v2/reply/report",
            {"reason": ReportReason.SPAM, "content": "  details  "},
            {"reason": ["3"], "content": ["details"]},
        ),
    ],
)
async def test_source_derived_write_forms(method, path, kwargs, extra):
    expected = {
        "type": ["12"],
        "oid": ["23199"],
        "rpid": ["2554491176"],
        "csrf": ["csrf-token"],
        **extra,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == path
        assert parse_qs(request.content.decode(), keep_blank_values=True) == expected
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        result = await getattr(client.comment, method)(
            comment_type=CommentType.ARTICLE,
            oid=23199,
            rpid=2554491176,
            **kwargs,
        )
    assert result is None


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("list", {"comment_type": 0, "oid": 1}),
        ("list", {"comment_type": 1, "oid": 1, "page_size": 21}),
        ("list", {"comment_type": 1, "oid": 1, "sort": 9}),
        ("replies", {"comment_type": 1, "oid": 1, "root": 0}),
        ("add", {"comment_type": 0, "oid": 1, "message": "x"}),
        ("add", {"comment_type": 1, "oid": 1, "message": " "}),
        ("like", {"comment_type": 1, "oid": 1, "rpid": 1, "action": 2}),
        ("report", {"comment_type": 1, "oid": 1, "rpid": 1, "reason": 18}),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=csrf-token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.comment, method)(**kwargs)


async def test_write_requires_csrf_after_validation():
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await client.comment.delete(comment_type=CommentType.VIDEO, oid=1, rpid=1)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("comment/")]
    assert len(paths) == 16
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_comment_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "comment"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.comment.") and api["status"] == "implemented"
    }
    assert len(expected) == 10
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(CommentClient, name, None)) for name in expected)
