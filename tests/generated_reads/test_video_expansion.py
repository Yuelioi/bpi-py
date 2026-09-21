from __future__ import annotations

import httpx
import pytest
from pydantic import ValidationError

from bpi import AsyncBpiClient, InvalidParameterError
from bpi._generated.video_models import PageInfo, VideoDetail, VideoDetailTag, VideoTag
from bpi.video.models import VideoView


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("No live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


@pytest.mark.parametrize(
    "method,kwargs,expected",
    [
        ("detail", {"aid": 2, "need_elec": False}, {"aid": "2", "need_elec": "0"}),
        ("detail", {"aid": 2}, {"aid": "2"}),
        (
            "series_archives",
            {
                "mid": 1,
                "series_id": 2,
                "only_normal": False,
                "sort": "desc",
                "page_num": 2,
                "page_size": 5,
            },
            {
                "mid": "1",
                "series_id": "2",
                "only_normal": "false",
                "sort": "desc",
                "pn": "2",
                "ps": "5",
            },
        ),
        ("series_archives", {"mid": 1, "series_id": 2}, {"mid": "1", "series_id": "2"}),
        (
            "seasons_archives_list",
            {"mid": 1, "season_id": 2},
            {"mid": "1", "season_id": "2", "page_num": "1", "page_size": "20"},
        ),
        ("home_seasons_series", {"mid": 1}, {"mid": "1", "page_num": "1", "page_size": "10"}),
        ("seasons_series_list", {"mid": 1}, {"mid": "1"}),
        (
            "interactive_video_info",
            {"aid": 2, "graph_version": 3, "edge_id": 4},
            {"aid": "2", "graph_version": "3", "edge_id": "4"},
        ),
    ],
)
async def test_nonfixture_parameter_variants(method, kwargs, expected):
    from bpi import ApiError

    def handler(request):
        if request.url.path.endswith("/nav"):
            return httpx.Response(
                200,
                json={
                    "code": -101,
                    "data": {
                        "wbi_img": {
                            "img_url": "https://example.invalid/abcdefghijklmnopqrstuvwxyz123456.png",
                            "sub_url": "https://example.invalid/ABCDEFGHIJKLMNOPQRSTUVWXYZ654321.png",
                        }
                    },
                },
            )
        actual = dict(request.url.params)
        for key in ("wts", "w_rid"):
            actual.pop(key, None)
        assert actual == expected
        return httpx.Response(200, json={"code": -400})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ApiError):
            await getattr(client.video, method)(**kwargs)


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("detail", {"aid": 2, "need_elec": 0}),
        ("series_archives", {"mid": 1, "series_id": 2, "only_normal": "true"}),
        ("series_archives", {"mid": 1, "series_id": 2, "sort": "random"}),
        ("series_archives", {"mid": 1, "series_id": 2, "page_num": 0}),
        ("seasons_archives_list", {"mid": 1, "season_id": 2, "page_size": False}),
        ("interactive_video_info", {"aid": 2, "graph_version": 0}),
        ("interactive_video_info", {"aid": 2, "graph_version": 1, "edge_id": 0}),
    ],
)
async def test_invalid_parameter_variants(method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.video, method)(**kwargs)


def test_pagination_aliases_and_strictness():
    canonical = PageInfo(page_num=1, page_size=20, total=40)
    assert PageInfo.model_validate({"num": 1, "size": 20, "total": 40}) == canonical
    assert canonical.model_dump(by_alias=True) == {"page_num": 1, "page_size": 20, "total": 40}
    with pytest.raises(ValidationError):
        PageInfo.model_validate({"num": "bad", "size": 20, "total": 40})


def test_detail_reuses_public_view_and_distinguishes_tag_models():
    assert VideoDetail.model_fields["view"].annotation is VideoView
    assert VideoDetailTag is not VideoTag
    assert "tag_type" not in VideoDetailTag.model_fields
    assert "tag_type" in VideoTag.model_fields
