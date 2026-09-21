from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import httpx
import pytest

from bpi import ApiError, AsyncBpiClient, InvalidParameterError
from bpi.video_ranking import VideoNewListRankOrder, VideoRankingClient, VideoRankingType

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
RANKING_FIXTURES = FIXTURES / "video_ranking/read"
WBI_BODY = {
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
        raise AssertionError("video_ranking tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


CASES = [
    ("popular-list", "popular_list", {"page": 1, "page_size": 2}),
    ("popular-series-list", "popular_series_list", {}),
    ("popular-series-one", "popular_series_one", {"number": 1}),
    ("popular-precious", "popular_precious", {}),
    (
        "ranking-list",
        "ranking_list",
        {"rid": 1, "ranking_type": VideoRankingType.ALL},
    ),
    ("region-dynamic", "region_dynamic", {"rid": 21, "page": 1, "page_size": 2}),
    (
        "region-tag-dynamic",
        "region_tag_dynamic",
        {"rid": 136, "tag_id": 10026108, "page": 1, "page_size": 2},
    ),
    (
        "region-newlist",
        "region_newlist",
        {"rid": 231, "page": 1, "page_size": 2, "typ": 1},
    ),
    (
        "region-newlist-rank",
        "region_newlist_rank",
        {
            "cate_id": 231,
            "page_size": 2,
            "time_from": "20260701",
            "time_to": "20260703",
            "order": VideoNewListRankOrder.CLICK,
            "page": 1,
        },
    ),
]


def _cookie(profile: str) -> str | None:
    return None if profile == "anonymous" else "SESSDATA=fake; bili_jct=token"


@pytest.mark.parametrize("directory,method,kwargs", CASES, ids=[case[0] for case in CASES])
async def test_promoted_contracts_all_profiles(directory, method, kwargs):
    contract = json.loads((RANKING_FIXTURES / directory / "contract.json").read_bytes())
    expected = contract["request"]

    for case in contract["cases"]:
        body = (RANKING_FIXTURES / directory / case["response"]["fixture"]).read_bytes()
        target_calls: list[httpx.Request] = []

        def handler(
            request: httpx.Request,
            *,
            body: bytes = body,
            target_calls: list[httpx.Request] = target_calls,
        ) -> httpx.Response:
            if request.url.path == "/x/web-interface/nav":
                return httpx.Response(200, json=WBI_BODY)

            target_calls.append(request)
            assert request.method == "GET"
            assert str(request.url).split("?")[0] == expected["url"]
            actual = dict(request.url.params)
            if contract["name"] == "video_ranking.popular_series_one":
                assert actual.pop("wts", "").isdigit()
                assert len(actual.pop("w_rid", "")) == 32
            assert actual == expected["query"]
            return httpx.Response(200, content=body)

        async with AsyncBpiClient(
            cookie=_cookie(case["profile"]),
            transport=httpx.MockTransport(handler),
            clock=lambda: 1700000000.0,
        ) as client:
            call = getattr(client.video_ranking, method)
            code = case["response"]["api_code"]
            if code == 0:
                assert await call(**kwargs) is not None
            else:
                with pytest.raises(ApiError) as error:
                    await call(**kwargs)
                assert error.value.code == code

        assert len(target_calls) == 1


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("popular_list", {"page": 0}),
        ("popular_series_one", {"number": 0}),
        ("ranking_list", {"rid": 0}),
        ("ranking_list", {"ranking_type": "invalid"}),
        ("region_dynamic", {"rid": 0}),
        ("region_tag_dynamic", {"rid": 1, "tag_id": 0}),
        ("region_newlist", {"rid": 1, "typ": 0}),
        (
            "region_newlist_rank",
            {"cate_id": 1, "page_size": 2, "time_from": " ", "time_to": "20260703"},
        ),
        (
            "region_newlist_rank",
            {
                "cate_id": 1,
                "page_size": 2,
                "time_from": "20260701",
                "time_to": "20260703",
                "order": "invalid",
            },
        ),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.video_ranking, method)(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("video_ranking/")]
    assert len(paths) == 36
    for rel in paths:
        assert (
            hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest() == provenance["sha256"][rel]
        )


def test_complete_video_ranking_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {
        method["name"] for method in inventory["methods"] if method["domain"] == "video_ranking"
    }
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.video_ranking.")
        and api["status"] == "implemented"
    }
    assert len(expected) == 9
    assert implemented == expected
    assert all(
        inspect.iscoroutinefunction(getattr(VideoRankingClient, name, None)) for name in expected
    )
