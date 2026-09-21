"""Source-derived offline cases for all previously uncontracted video actions.

Wire expectations follow bpi-rs video/action.rs, report.rs and collection/action.rs.
Response bodies below are synthetic, not recorded live responses.
"""

import json
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest

from bpi import ApiError, AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.errors import HttpStatusError, MissingDataError, ResponseDecodeError, TransportError


def test_video_module_covers_every_source_method():
    from bpi.video.client import VideoClient

    root = Path(__file__).resolve().parents[2]
    inventory = json.loads((root / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((root / "migration/python-api.json").read_bytes())
    expected = {m["name"] for m in inventory["methods"] if m["domain"] == "video"}
    implemented = {
        m["python"].rsplit(".", 1)[1]
        for m in mapping["apis"]
        if m["python"].startswith("AsyncBpiClient.video.")
    }
    assert len(expected) == 27
    assert implemented == expected
    assert all(callable(getattr(VideoClient, name, None)) for name in expected)


# method, kwargs, path, encoding, query, body, required payload
WRITES = [
    (
        "like",
        {"aid": 1, "like": 2},
        "/x/web-interface/archive/like",
        "form",
        {},
        {"aid": "1", "like": "2", "csrf": "token"},
        None,
    ),
    (
        "coin",
        {"bvid": "legacy-bv", "multiply": 2, "select_like": True},
        "/x/web-interface/coin/add",
        "form",
        {},
        {"bvid": "legacy-bv", "multiply": "2", "select_like": "1", "csrf": "token"},
        {"like": True},
    ),
    (
        "favorite",
        {"rid": 1, "add_media_ids": [" 2 ", "3"], "del_media_ids": ["4"]},
        "/x/v3/fav/resource/deal",
        "form",
        {},
        {"rid": "1", "type": "2", "add_media_ids": "2,3", "del_media_ids": "4", "csrf": "token"},
        {"prompt": False, "success_num": 1},
    ),
    (
        "report_watch_progress",
        {"aid": 1, "cid": 2},
        "/x/v2/history/report",
        "multipart",
        {},
        {"aid": "1", "cid": "2", "progress": "0", "csrf": "token"},
        None,
    ),
    (
        "create_collection_series",
        {"mid": 1, "name": " 中文 ", "keywords": " a,b ", "description": " desc ", "aids": "2,3"},
        "/x/series/series/createAndAddArchives",
        "multipart",
        {"csrf": "token"},
        {"mid": "1", "name": "中文", "keywords": "a,b", "description": "desc", "aids": "2,3"},
        {"series_id": 123},
    ),
    (
        "delete_collection_series",
        {"mid": 1, "series_id": 2},
        "/x/series/series/delete",
        "empty",
        {"csrf": "token", "mid": "1", "series_id": "2", "aids": ""},
        {},
        None,
    ),
    (
        "delete_collection_archives",
        {"mid": 1, "series_id": 2, "aids": " 3,4 "},
        "/x/series/series/delArchives",
        "form",
        {"csrf": "token"},
        {"mid": "1", "series_id": "2", "aids": "3,4"},
        None,
    ),
    (
        "add_collection_archives",
        {"mid": 1, "series_id": 2, "aids": "3,4"},
        "/x/series/series/addArchives",
        "form",
        {"csrf": "token"},
        {"mid": "1", "series_id": "2", "aids": "3,4"},
        None,
    ),
    (
        "update_collection_series",
        {
            "mid": 1,
            "series_id": 2,
            "name": " 新标题 ",
            "keywords": "tag",
            "description": "desc",
            "add_aids": "3",
            "del_aids": "4",
        },
        "/x/series/series/update",
        "multipart",
        {"csrf": "token"},
        {
            "mid": "1",
            "series_id": "2",
            "name": "新标题",
            "keywords": "tag",
            "description": "desc",
            "add_aids": "3",
            "del_aids": "4",
        },
        None,
    ),
]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("No live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def body_fields(request, encoding):
    if encoding == "empty":
        assert request.content == b""
        return {}
    if encoding == "form":
        assert request.headers["content-type"] == "application/x-www-form-urlencoded"
        return dict(parse_qsl(request.content.decode(), keep_blank_values=True))
    content_type = request.headers["content-type"]
    assert content_type.startswith("multipart/form-data; boundary=")
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode() + request.content
    )
    parts = list(message.iter_parts())
    assert all(p.get_filename() is None for p in parts)
    return {
        p.get_param("name", header="content-disposition"): p.get_payload(decode=True).decode()
        for p in parts
    }


@pytest.mark.parametrize("case", WRITES, ids=[x[0] for x in WRITES])
@pytest.mark.parametrize("response_kind", ["success", "error", "missing"])
async def test_write_protocol(case, response_kind):
    name, kwargs, path, encoding, query, form, payload = case
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "POST"
        assert request.url.host == "api.bilibili.com" and request.url.path == path
        assert dict(request.url.params) == query
        assert "bili_jct=token" in request.headers["cookie"]
        assert body_fields(request, encoding) == form
        body = {"code": 0, "data": payload}
        if response_kind == "error":
            body = {"code": -403, "message": "denied", "data": "invalid"}
        elif response_kind == "missing":
            body = {"code": 0}
        return httpx.Response(200, json=body)

    async with AsyncBpiClient(
        cookie="bili_jct=token; SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        method = getattr(client.video, name)
        if response_kind == "error":
            with pytest.raises(ApiError) as error:
                await method(**kwargs)
            assert error.value.code == -403
        elif response_kind == "missing" and payload is not None:
            with pytest.raises(MissingDataError):
                await method(**kwargs)
        else:
            result = await method(**kwargs)
            if payload is None:
                assert result is None
            else:
                assert all(result.model_dump()[k] == v for k, v in payload.items())
    assert len(calls) == 1


@pytest.mark.parametrize("case", WRITES, ids=[x[0] for x in WRITES])
async def test_writes_require_csrf_before_network(case):
    async with AsyncBpiClient() as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.video, case[0])(**case[1])


@pytest.mark.parametrize(
    "name,kwargs",
    [
        ("coin_status", {}),
        ("coin_status", {"aid": True}),
        ("like", {"aid": 1, "like": 3}),
        ("like", {"aid": 1, "like": True}),
        ("coin", {"aid": 1, "multiply": 3}),
        ("coin", {"aid": 1, "multiply": 1, "select_like": 1}),
        ("favorite", {"rid": 1}),
        ("favorite", {"rid": 1, "add_media_ids": "123"}),
        ("favorite", {"rid": 1, "add_media_ids": [" "]}),
        ("report_watch_progress", {"aid": 1, "cid": 2, "progress": -1}),
        ("create_collection_series", {"mid": 1, "name": " "}),
        ("delete_collection_series", {"mid": 0, "series_id": 2}),
        ("delete_collection_archives", {"mid": 1, "series_id": 2, "aids": " "}),
        ("add_collection_archives", {"mid": 1, "series_id": False, "aids": "3"}),
        ("update_collection_series", {"mid": 1, "series_id": 2, "name": "n", "add_aids": ""}),
        ("homepage_recommendations", {"page_size": 31}),
        ("homepage_recommendations", {"fresh_idx": 0}),
        ("player_info_v2", {"aid": 1, "cid": 2, "season_id": 0}),
    ],
)
async def test_invalid_module_arguments(name, kwargs):
    async with AsyncBpiClient(cookie="bili_jct=token") as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.video, name)(**kwargs)


async def test_coin_status_legacy_ids():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/x/web-interface/archive/coins"
        assert dict(request.url.params) == {"aid": "1", "bvid": "legacy"}
        return httpx.Response(200, json={"code": 0, "data": {"multiply": 2}})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        assert (await client.video.coin_status(aid=1, bvid="legacy")).multiply == 2


@pytest.mark.parametrize("mode", ["redirect", "transport", "decode", "optional_value"])
async def test_post_transport_and_optional_payload(mode):
    calls = []

    def handler(request):
        calls.append(request)
        assert dict(request.url.params) == {}  # borrowed defaults must not leak into writes
        if mode == "redirect":
            return httpx.Response(302, headers={"location": "https://example.invalid"})
        if mode == "transport":
            raise httpx.ConnectError("secret-token", request=request)
        if mode == "decode":
            return httpx.Response(200, content=b'{"code":0,"data":{"like":"secret-token"}}')
        return httpx.Response(200, json={"code": 0, "result": {"ok": True}})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
        params={"unexpected": "value"},
        cookies={"bili_jct": "token"},
    ) as http:
        async with AsyncBpiClient(http_client=http) as client:
            if mode == "optional_value":
                assert await client.video.like(aid=1, like=1) == {"ok": True}
            else:
                expected = {
                    "redirect": HttpStatusError,
                    "transport": TransportError,
                    "decode": ResponseDecodeError,
                }[mode]
                with pytest.raises(expected) as error:
                    await client.video.coin(aid=1, multiply=1)
                assert "secret-token" not in str(error.value)
        assert not http.is_closed
    assert len(calls) == 1


async def test_new_read_nondefault_query_signing():
    from bpi.sign.wbi import sign_params

    img, sub, now = "a" * 32, "b" * 32, 1700000000
    calls = []

    def handler(request):
        if request.url.path.endswith("/nav"):
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "data": {
                        "wbi_img": {
                            "img_url": f"https://example.invalid/{img}.png",
                            "sub_url": f"https://example.invalid/{sub}.png",
                        }
                    },
                },
            )
        calls.append(request)
        expected = (
            {
                "fresh_type": "4",
                "ps": "30",
                "fresh_idx": "3",
                "fresh_idx_1h": "3",
                "brush": "3",
                "fetch_row": "2",
            }
            if request.url.path.endswith("/rcmd")
            else {"aid": "1", "cid": "2", "season_id": "3", "ep_id": "4"}
        )
        assert dict(request.url.params) == sign_params(expected, img, sub, now)
        return httpx.Response(200, json={"code": -400})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler), clock=lambda: now) as client:
        with pytest.raises(ApiError):
            await client.video.homepage_recommendations(page_size=30, fresh_idx=3, fetch_row=2)
        with pytest.raises(ApiError):
            await client.video.player_info_v2(aid=1, cid=2, season_id=3, ep_id=4)
    assert len(calls) == 2
