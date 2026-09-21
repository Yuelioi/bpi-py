from __future__ import annotations

import base64
import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest

from bpi import ApiError, AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.creativecenter import (
    CreativeCenterClient,
    Episode,
    EpisodeAdd,
    EpisodeEdit,
    EpisodeSort,
    SeasonEdit,
    SeasonListOrder,
    SeasonListSort,
    SeasonSectionEdit,
    SeasonSectionSort,
    SectionSort,
    UpArticleTrendMetric,
    UpVideoTrendMetric,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
CREATIVE_FIXTURES = FIXTURES / "creativecenter/read"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("creativecenter tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def _contract(path: str) -> dict[str, object]:
    return json.loads((CREATIVE_FIXTURES / path / "contract.json").read_bytes())


def _response(path: str, filename: str) -> bytes:
    return (CREATIVE_FIXTURES / path / "responses" / filename).read_bytes()


READ_CASES = [
    (
        "season/list",
        "season_list",
        {"pn": 1, "ps": 10, "order": SeasonListOrder.CREATED_AT, "sort": SeasonListSort.DESC},
    ),
    ("season/info", "season_info", {"season_id": 4_294_056}),
    ("season/aid", "season_by_aid", {"aid": 113_602_455_409_683}),
    ("season/section", "season_section_episodes", {"season_id": 176_088}),
    ("videos/archives-list", "archives_list", {"pn": 1, "ps": 10}),
    ("videos/archive-videos", "archive_videos", {"aid": 113_602_455_409_683}),
    ("statistics/up-stat", "up_stat", {}),
    ("statistics/archive-compare", "archive_compare", {"size": 3}),
    ("statistics/article-stat", "article_stat", {}),
    ("statistics/video-trend", "video_trend", {"metric": UpVideoTrendMetric.PLAY}),
    ("statistics/article-trend", "article_trend", {"metric": UpArticleTrendMetric.READ}),
    ("statistics/play-source", "play_source", {}),
    ("statistics/viewer-data", "viewer_data", {}),
    ("railgun-read/electromagnetic-info", "electromagnetic_info", {}),
]


def _assert_request(request: httpx.Request, contract: dict[str, object]) -> None:
    spec = contract["request"]
    assert request.method == spec["method"]
    assert str(request.url).split("?")[0] == spec["url"]
    assert dict(request.url.params) == spec["query"]
    for header in spec["required_headers"]:
        assert header.lower() in request.headers
    for key, value in spec["headers"].items():
        assert request.headers[key] == value


@pytest.mark.parametrize("fixture_path,method,kwargs", READ_CASES)
async def test_promoted_read_success_cases(
    fixture_path: str, method: str, kwargs: dict[str, object]
):
    contract = _contract(fixture_path)
    success_cases = [case for case in contract["cases"] if case["response"].get("error") is None]
    assert success_cases

    for case in success_cases:
        body = _response(fixture_path, Path(case["response"]["fixture"]).name)

        def handler(request: httpx.Request, response_body: bytes = body) -> httpx.Response:
            _assert_request(request, contract)
            return httpx.Response(200, content=response_body)

        cookie = None if case["profile"] == "anonymous" else "SESSDATA=fake"
        async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
            result = await getattr(client.creativecenter, method)(**kwargs)

        if method == "play_source" or (method == "article_trend" and case["profile"] == "normal"):
            assert result is None
        else:
            assert result is not None


@pytest.mark.parametrize("fixture_path,method,kwargs", READ_CASES)
async def test_promoted_read_error_cases(
    fixture_path: str, method: str, kwargs: dict[str, object]
):
    contract = _contract(fixture_path)
    error_cases = [case for case in contract["cases"] if case["response"].get("error")]
    for case in error_cases:
        body = _response(fixture_path, Path(case["response"]["fixture"]).name)

        def handler(request: httpx.Request, response_body: bytes = body) -> httpx.Response:
            _assert_request(request, contract)
            return httpx.Response(200, content=response_body)

        cookie = None if case["profile"] == "anonymous" else "SESSDATA=fake"
        error_type = (
            AuthenticationError if case["response"]["error"] == "requires_login" else ApiError
        )
        async with AsyncBpiClient(cookie=cookie, transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(error_type) as exc:
                await getattr(client.creativecenter, method)(**kwargs)
        assert exc.value.code == case["response"]["api_code"]


def _form(request: httpx.Request) -> dict[str, str]:
    return dict(parse_qsl(request.content.decode()))


async def test_dynamic_delete_source_derived_json_request():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/dynamic/feed/operate/remove"
        assert dict(request.url.params) == {"csrf": "csrf-token"}
        assert json.loads(request.content) == {"dyn_id_str": "123"}
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await client.creativecenter.dynamic_delete(dyn_id=" 123 ") is None


async def test_article_delete_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "member.bilibili.com"
        assert request.url.path == "/x/web/article/delete"
        assert _form(request) == {"aid": "42", "csrf": "csrf-token"}
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await client.creativecenter.article_delete(aid=42) is None


@pytest.mark.parametrize(
    "cover,expected",
    [
        ("data:image/png;base64,QUJD", "data:image/png;base64,QUJD"),
        ("QUJD", "data:image/png;base64,QUJD"),
    ],
)
async def test_upload_cover_data_uri_and_base64(cover: str, expected: str):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "member.bilibili.com"
        assert request.url.path == "/x/vu/web/cover/up"
        assert _form(request) == {"csrf": "csrf-token", "cover": expected}
        return httpx.Response(200, json={"code": 0, "data": {"url": "https://example.invalid/a"}})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.creativecenter.upload_cover(mime_type="image/png", cover=cover)
    assert result.url == "https://example.invalid/a"


async def test_upload_cover_file_path(tmp_path: Path):
    image = tmp_path / "cover.png"
    image.write_bytes(b"image-bytes")
    expected = "data:image/png;base64," + base64.b64encode(b"image-bytes").decode()

    def handler(request: httpx.Request) -> httpx.Response:
        assert _form(request)["cover"] == expected
        return httpx.Response(200, json={"code": 0, "data": {"url": "https://example.invalid/b"}})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.creativecenter.upload_cover(mime_type="image/png", cover=image)
    assert result.url == "https://example.invalid/b"


async def test_season_create_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x2/creative/web/season/add"
        assert _form(request) == {
            "title": "合集",
            "cover": "https://example.invalid/cover.jpg",
            "csrf": "csrf-token",
            "desc": "简介",
            "season_price": "0",
        }
        return httpx.Response(200, json={"code": 0, "data": 99})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.creativecenter.season_create(
            title=" 合集 ", cover=" https://example.invalid/cover.jpg ", desc="简介", season_price=0
        )
    assert result == 99


async def test_season_delete_and_enable_section_forms():
    seen = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen
        seen += 1
        if request.url.path.endswith("/season/del"):
            assert _form(request) == {"id": "9", "csrf": "csrf-token"}
        else:
            assert request.url.path.endswith("/season/section/switch")
            assert _form(request) == {
                "csrf": "csrf-token",
                "season_id": "9",
                "no_section": "0",
            }
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await client.creativecenter.season_delete(season_id=9) is None
        assert await client.creativecenter.season_enable_section(season_id=9, enable=True) is None
    assert seen == 2


async def test_season_episode_add_variants_source_derived_json():
    seen = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen
        seen += 1
        assert request.url.path == "/x2/creative/web/season/section/episodes/add"
        assert dict(request.url.params) == {"csrf": "csrf-token"}
        body = json.loads(request.content)
        assert body["sectionId"] == 7
        assert body["episodes"][0]["title"] == "第一集"
        assert body["episodes"][0]["aid"] == 11
        assert body["episodes"][0]["cid"] == 12
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert await client.creativecenter.season_episodes_add(
            section_id=7, episodes=[EpisodeAdd(title="第一集", aid=11, cid=12)]
        ) is None
        assert await client.creativecenter.season_section_add_episodes(
            section_id=7,
            episodes=[
                Episode(
                    title="第一集",
                    aid=11,
                    cid=12,
                    charging_pay=0,
                    member_first=0,
                    limited_free=False,
                )
            ],
        ) is None
    assert seen == 2


async def test_season_edit_requests_source_derived_json():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert dict(request.url.params) == {"csrf": "csrf-token"}
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="bili_jct=csrf-token", transport=httpx.MockTransport(handler)
    ) as client:
        await client.creativecenter.season_edit(
            season=SeasonEdit(id=1, title="合集", cover="cover", isEnd=1),
            sorts=[SeasonSectionSort(id=2, sort=3)],
        )
        await client.creativecenter.season_section_edit(
            section=SeasonSectionEdit(id=2, type=1, seasonId=1, title="小节"),
            sorts=[SectionSort(id=4, order=5)],
        )
        await client.creativecenter.season_section_episode_edit(
            episode=EpisodeEdit(
                id=4,
                title="视频",
                aid=11,
                cid=12,
                seasonId=1,
                sectionId=2,
                sorts=[EpisodeSort(id=99, sort=99)],
                order=1,
            ),
            sorts=[EpisodeSort(id=4, sort=6)],
        )

    first, second, third = requests
    assert first.url.path.endswith("/season/edit")
    assert json.loads(first.content)["season"]["isEnd"] == 1
    assert json.loads(first.content)["sorts"] == [{"id": 2, "sort": 3}]
    assert second.url.path.endswith("/season/section/edit")
    assert json.loads(second.content)["section"] == {
        "id": 2,
        "type": 1,
        "seasonId": 1,
        "title": "小节",
    }
    assert third.url.path.endswith("/season/section/episode/edit")
    assert json.loads(third.content)["sorts"] == [{"id": 4, "sort": 6}]


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("season_list", {"pn": 0, "ps": 10}),
        ("season_list", {"pn": 1, "ps": 0}),
        ("archives_list", {"pn": 1, "ps": 0}),
        ("archive_compare", {"timestamp": 0}),
        ("archive_compare", {"size": 0}),
        ("video_trend", {"metric": 0}),
        ("article_trend", {"metric": 0}),
        ("dynamic_delete", {"dyn_id": "   "}),
        ("article_delete", {"aid": 0}),
        ("upload_cover", {"mime_type": " ", "cover": "QUJD"}),
        ("upload_cover", {"mime_type": "image/png", "cover": " "}),
        ("season_create", {"title": " ", "cover": "cover"}),
        ("season_create", {"title": "title", "cover": " "}),
        ("season_create", {"title": "title", "cover": "cover", "season_price": -1}),
        ("season_delete", {"season_id": 0}),
        ("season_episodes_add", {"section_id": 1, "episodes": []}),
        ("season_section_add_episodes", {"section_id": 1, "episodes": []}),
        ("season_enable_section", {"season_id": 1, "enable": 1}),
    ],
)
async def test_invalid_arguments_fail_before_network(method: str, kwargs: dict[str, object]):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.creativecenter, method)(**kwargs)


async def test_missing_cover_file_fails_before_csrf(tmp_path: Path):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await client.creativecenter.upload_cover(
                mime_type="image/png", cover=tmp_path / "missing.png"
            )


async def test_valid_write_requires_csrf_after_validation():
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await client.creativecenter.dynamic_delete(dyn_id="1")


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("creativecenter/read/")]
    assert len(paths) == 56
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_creativecenter_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {
        method["name"] for method in inventory["methods"] if method["domain"] == "creativecenter"
    }
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.creativecenter.")
        and api["status"] == "implemented"
    }
    assert len(expected) == 25
    assert implemented == expected
    assert all(
        inspect.iscoroutinefunction(getattr(CreativeCenterClient, name, None)) for name in expected
    )
