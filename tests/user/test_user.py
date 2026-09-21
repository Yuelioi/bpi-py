"""User module coverage. Read evidence is promoted; write responses are synthetic offline data."""

from __future__ import annotations

import hashlib
import inspect
import json
from email.parser import BytesParser
from email.policy import default
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from bpi import ApiError, AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi._generated.user_models import (
    UserBatchInfo,
    UserCardSummary,
    UserFollowings,
    UserNameToUidItem,
    UserNavStat,
)
from bpi.user.client import UserClient
from bpi.user.models import UserSpaceNotice, UserUpStat

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("User tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def multipart_fields(request: httpx.Request) -> dict[str, str]:
    content_type = request.headers["content-type"]
    assert content_type.startswith("multipart/form-data; boundary=")
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode() + request.content
    )
    parts = list(message.iter_parts())
    assert all(part.get_filename() is None for part in parts)
    return {
        part.get_param("name", header="content-disposition"): part.get_payload(decode=True).decode()
        for part in parts
    }


# method, kwargs, path, expected multipart fields, synthetic success payload
WRITES = [
    (
        "modify_relation",
        {"fid": 2, "action": 1, "source": 14},
        "/x/relation/modify",
        {"fid": "2", "act": "1", "re_src": "14", "csrf": "token"},
        None,
    ),
    (
        "create_group_tag",
        {"group_name": " 中文 "},
        "/x/relation/tag/create",
        {"tag": "中文", "csrf": "token"},
        {"tagid": 123},
    ),
    (
        "update_group_tag",
        {"tag_id": 4, "new_name": " new "},
        "/x/relation/tag/update",
        {"tagid": "4", "name": "new", "csrf": "token"},
        None,
    ),
    (
        "delete_group_tag",
        {"tag_id": 4},
        "/x/relation/tag/del",
        {"tagid": "4", "csrf": "token"},
        None,
    ),
    (
        "add_group_users_to_tags",
        {"fids": [2, 3], "tag_ids": [4, 5]},
        "/x/relation/tags/addUsers",
        {"fids": "2,3", "tagids": "4,5", "csrf": "token"},
        None,
    ),
    (
        "remove_group_users",
        {"fids": [2, 3]},
        "/x/relation/tags/addUsers",
        {"fids": "2,3", "tagids": "0", "csrf": "token"},
        None,
    ),
    (
        "copy_group_users_to_tags",
        {"fids": [2], "tag_ids": [4]},
        "/x/relation/tags/copyUsers",
        {"fids": "2", "tagids": "4", "csrf": "token"},
        None,
    ),
    (
        "move_group_users_to_tags",
        {"fids": [2], "before_tag_ids": [4], "after_tag_ids": [5]},
        "/x/relation/tags/moveUsers",
        {"fids": "2", "beforeTagids": "4", "afterTagids": "5", "csrf": "token"},
        None,
    ),
    (
        "set_space_notice",
        {"notice": "hello"},
        "/x/space/notice/set",
        {"notice": "hello", "csrf": "token"},
        None,
    ),
]


@pytest.mark.parametrize("case", WRITES, ids=[case[0] for case in WRITES])
@pytest.mark.parametrize("response_kind", ["success", "error"])
async def test_write_protocol_is_source_derived(case, response_kind):
    name, kwargs, path, expected_form, payload = case
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "POST" and request.url.path == path
        assert request.url.host == "api.bilibili.com" and dict(request.url.params) == {}
        assert "bili_jct=token" in request.headers.get("cookie", "")
        assert multipart_fields(request) == expected_form
        if response_kind == "error":
            return httpx.Response(200, json={"code": -403, "message": "denied"})
        return httpx.Response(200, json={"code": 0, "data": payload})

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=token", transport=httpx.MockTransport(handler)
    ) as client:
        method = getattr(client.user, name)
        if response_kind == "error":
            with pytest.raises(ApiError) as error:
                await method(**kwargs)
            assert error.value.code == -403
        else:
            result = await method(**kwargs)
            if name == "create_group_tag":
                assert result.tagid == 123
            else:
                assert result is None
    assert len(calls) == 1


@pytest.mark.parametrize("case", WRITES, ids=[case[0] for case in WRITES])
async def test_writes_require_csrf_before_network(case):
    async with AsyncBpiClient() as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.user, case[0])(**case[1])


@pytest.mark.parametrize(
    "name,kwargs",
    [
        ("modify_relation", {"fid": 0, "action": 1}),
        ("modify_relation", {"fid": 2, "action": 8}),
        ("modify_relation", {"fid": 2, "action": 1, "source": 2}),
        ("create_group_tag", {"group_name": " "}),
        ("create_group_tag", {"group_name": "中" * 6}),
        ("update_group_tag", {"tag_id": 0, "new_name": "x"}),
        ("add_group_users_to_tags", {"fids": [], "tag_ids": [1]}),
        ("copy_group_users_to_tags", {"fids": [1], "tag_ids": [0]}),
        (
            "move_group_users_to_tags",
            {"fids": [1], "before_tag_ids": [], "after_tag_ids": [2]},
        ),
        ("set_space_notice", {"notice": "中" * 51}),
    ],
)
async def test_invalid_write_arguments_fail_before_network(name, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.user, name)(**kwargs)


def test_user_model_compatibility_rules():
    assert UserCardSummary.model_validate({"mid": "2", "name": "n", "face": "f"}).mid == 2
    assert UserNameToUidItem.model_validate({"name": "n", "uid": "3"}).mid == 3
    with pytest.raises(ValidationError):
        UserNameToUidItem.model_validate({"name": "n", "uid": 0})

    info = UserBatchInfo.model_validate({"mid": 2, "name": "n", "face": "f", "sex": "  "})
    assert info.sex is None
    assert UserFollowings.model_validate({}).list == []
    nav = UserNavStat.model_validate({})
    assert nav.channel.master == 0 and nav.favourite.guest == 0
    assert UserUpStat.model_validate({}).likes == 0
    assert UserSpaceNotice.model_validate("notice").content == "notice"


def test_user_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("user/")]
    assert len(paths) == 41
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
            == provenance["sha256"][rel]
        )


def test_complete_user_module_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "user"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.user.") and api["status"] == "implemented"
    }
    assert len(expected) == 25
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(UserClient, name, None)) for name in expected)
