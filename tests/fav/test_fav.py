from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest
from pydantic import ValidationError

from bpi import ApiError, AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.fav import FavClient, FavListDetailData

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
FAV_FIXTURES = FIXTURES / "fav"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Fav tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


READS = [
    ("folder-info", "folder_info", {"media_id": 1052622027}),
    ("created-list", "created_list", {"up_mid": 7792521}),
    ("collected-list", "collected_list", {"up_mid": 7792521}),
    ("resource-infos", "resource_infos", {"resources": "371494037:2"}),
    (
        "list-detail",
        "list_detail",
        {
            "media_id": 1052622027,
            "order": "mtime",
            "content_type": 0,
            "page_size": 5,
            "page": 1,
        },
    ),
    ("resource-ids", "resource_ids", {"media_id": 1052622027}),
]


@pytest.mark.parametrize("directory,method,kwargs", READS, ids=[case[0] for case in READS])
async def test_promoted_read_contracts(directory, method, kwargs):
    contract = json.loads((FAV_FIXTURES / directory / "contract.json").read_bytes())
    fixture = contract["cases"][0]["response"]["fixture"]
    body = (FAV_FIXTURES / directory / fixture).read_bytes()
    calls = []

    def handler(request):
        calls.append(request)
        expected = contract["request"]
        assert request.method == expected["method"]
        assert str(request.url).split("?")[0] == expected["url"]
        assert dict(request.url.params) == expected["query"]
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await getattr(client.fav, method)(**kwargs)

    assert result is not None
    assert len(calls) == 1


WRITES = [
    (
        "add_folder",
        {"title": " folder ", "intro": "intro", "privacy": 1, "cover": "cover"},
        "/x/v3/fav/folder/add",
        {
            "title": "folder",
            "csrf": "token",
            "intro": "intro",
            "privacy": "1",
            "cover": "cover",
        },
        "folder",
    ),
    (
        "edit_folder",
        {"media_id": 1, "title": "renamed", "privacy": 0},
        "/x/v3/fav/folder/edit",
        {"media_id": "1", "title": "renamed", "csrf": "token", "privacy": "0"},
        "folder",
    ),
    (
        "delete_folders",
        {"media_ids": [1, 2]},
        "/x/v3/fav/folder/del",
        {"media_ids": "1,2", "csrf": "token"},
        "int",
    ),
    (
        "copy_resources",
        {"src_media_id": 1, "tar_media_id": 2, "mid": 3, "resources": "4:2"},
        "/x/v3/fav/resource/copy",
        {
            "src_media_id": "1",
            "tar_media_id": "2",
            "mid": "3",
            "resources": "4:2",
            "platform": "web",
            "csrf": "token",
        },
        "int",
    ),
    (
        "move_resources",
        {"src_media_id": 1, "tar_media_id": 2, "mid": 3, "resources": "4:2"},
        "/x/v3/fav/resource/move",
        {
            "src_media_id": "1",
            "tar_media_id": "2",
            "mid": "3",
            "resources": "4:2",
            "platform": "web",
            "csrf": "token",
        },
        "int",
    ),
    (
        "delete_resources",
        {"media_id": 1, "resources": "4:2"},
        "/x/v3/fav/resource/batch-del",
        {"media_id": "1", "resources": "4:2", "platform": "web", "csrf": "token"},
        "int",
    ),
    (
        "clean_resources",
        {"media_id": 1},
        "/x/v3/fav/resource/clean",
        {"media_id": "1", "csrf": "token"},
        "int",
    ),
]


@pytest.mark.parametrize("case", WRITES, ids=[case[0] for case in WRITES])
@pytest.mark.parametrize("response_kind", ["success", "error"])
async def test_write_protocol_is_source_derived(case, response_kind):
    name, kwargs, path, expected_form, payload_kind = case
    calls = []
    folder_payload = json.loads(
        (FAV_FIXTURES / "folder-info/responses/success.json").read_bytes()
    )["data"]

    def handler(request):
        calls.append(request)
        assert request.method == "POST"
        assert request.url.host == "api.bilibili.com"
        assert request.url.path == path
        assert dict(request.url.params) == {}
        assert request.headers["content-type"].startswith(
            "application/x-www-form-urlencoded"
        )
        actual = dict(parse_qsl(request.content.decode(), keep_blank_values=True))
        assert actual == expected_form
        assert "bili_jct=token" in request.headers.get("cookie", "")
        if response_kind == "error":
            return httpx.Response(200, json={"code": -403, "message": "denied"})
        payload = folder_payload if payload_kind == "folder" else 1
        return httpx.Response(200, json={"code": 0, "data": payload})

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=token",
        transport=httpx.MockTransport(handler),
    ) as client:
        method = getattr(client.fav, name)
        if response_kind == "error":
            with pytest.raises(ApiError) as error:
                await method(**kwargs)
            assert error.value.code == -403
        else:
            result = await method(**kwargs)
            if payload_kind == "folder":
                assert result.id == folder_payload["id"]
            else:
                assert result == 1 and type(result) is int
    assert len(calls) == 1


@pytest.mark.parametrize("case", WRITES, ids=[case[0] for case in WRITES])
async def test_writes_require_csrf_before_network(case):
    async with AsyncBpiClient() as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.fav, case[0])(**case[1])


@pytest.mark.parametrize(
    "name,kwargs",
    [
        ("folder_info", {"media_id": 0}),
        ("created_list", {"up_mid": 0}),
        ("created_list", {"up_mid": 1, "type_id": 256}),
        ("created_list", {"up_mid": 1, "resource_id": 0}),
        ("created_list", {"up_mid": 1, "web_location": " "}),
        ("collected_list", {"up_mid": 1, "page": 0}),
        ("collected_list", {"up_mid": 1, "page_size": False}),
        ("resource_infos", {"resources": " "}),
        ("resource_ids", {"media_id": 1, "platform": " "}),
        ("list_detail", {"media_id": 1, "page_size": 0}),
        ("list_detail", {"media_id": 1, "page": 0}),
        ("list_detail", {"media_id": 1, "keyword": " "}),
        ("list_detail", {"media_id": 1, "content_type": True}),
        ("add_folder", {"title": " "}),
        ("add_folder", {"title": "x", "privacy": 2}),
        ("edit_folder", {"media_id": 0, "title": "x"}),
        ("delete_folders", {"media_ids": []}),
        ("delete_folders", {"media_ids": [1, 0]}),
        (
            "copy_resources",
            {"src_media_id": 1, "tar_media_id": 2, "mid": 3, "resources": " "},
        ),
        ("delete_resources", {"media_id": 1, "resources": " "}),
        ("clean_resources", {"media_id": False}),
    ],
)
async def test_invalid_arguments_fail_before_network(name, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.fav, name)(**kwargs)


def test_list_detail_null_medias_matches_rust_serde():
    source = json.loads(
        (FAV_FIXTURES / "list-detail/responses/success.json").read_bytes()
    )["data"]
    source["medias"] = None
    assert FavListDetailData.model_validate(source).medias == []
    source["info"]["id"] = "1052622027"
    with pytest.raises(ValidationError):
        FavListDetailData.model_validate(source)


def test_fav_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("fav/")]
    assert len(paths) == 12
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_fav_module_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {
        method["name"] for method in inventory["methods"] if method["domain"] == "fav"
    }
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.fav.")
        and api["status"] == "implemented"
    }
    assert len(expected) == 13
    assert implemented == expected
    assert all(
        inspect.iscoroutinefunction(getattr(FavClient, name, None))
        for name in expected
    )
