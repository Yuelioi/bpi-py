from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from bpi import (
    ApiError,
    AsyncBpiClient,
    HttpStatusError,
    InvalidParameterError,
    ResponseDecodeError,
)
from bpi._generated.bangumi_models import BangumiInfoResult
from bpi._generated.video_models import VideoTag
from bpi.sign.wbi import sign_params

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
BATCH = json.loads((ROOT / "migration/generated/batch-3.json").read_text(encoding="utf8"))
IMG = "abcdefghijklmnopqrstuvwxyz123456"
SUB = "ABCDEFGHIJKLMNOPQRSTUVWXYZ654321"
NOW = 1_700_000_000


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("No live network in generated read tests")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


def cases():
    for recipe in BATCH["cases"]:
        path = FIXTURES / Path(recipe["contract_path"]).relative_to("tests/contracts")
        contract = json.loads(path.read_bytes())
        for case in contract["cases"]:
            yield pytest.param(
                recipe, contract, case, path.parent, id=f"{contract['name']}:{case['name']}"
            )


@pytest.mark.parametrize("recipe,contract,case,folder", list(cases()))
async def test_generated_public_method_against_contract(recipe, contract, case, folder):
    calls = []
    response_case = case["response"]
    if "fixture" in response_case:
        body = (folder / response_case["fixture"]).read_bytes()
    else:
        assert response_case["fixture_kind"] == "local_probe_blocked"
        assert response_case["http_status"] >= 400
        body = b""  # Only recorded HTTP metadata is available; do not invent a payload.
    authenticated = case.get("profile") != "anonymous"

    def handler(request):
        calls.append(request.url.path)
        if recipe["signed"] and request.url.path.endswith("/nav"):
            return httpx.Response(
                200,
                json={
                    "code": -101,
                    "data": {
                        "wbi_img": {
                            "img_url": f"https://example.invalid/{IMG}.png",
                            "sub_url": f"https://example.invalid/{SUB}.png",
                        }
                    },
                },
            )
        expected = contract["request"]
        assert str(request.url).split("?")[0] == expected["url"]
        assert request.method == expected["method"]
        assert all(header in request.headers for header in expected["required_headers"])
        assert ("SESSDATA=test-session" in request.headers.get("cookie", "")) == authenticated
        expected_query = {
            key: ("test-csrf" if authenticated else "") if value == "${csrf}" else value
            for key, value in expected["query"].items()
        }
        if recipe["signed"]:
            expected_query = sign_params(expected_query, IMG, SUB, NOW)
        assert dict(request.url.params) == expected_query
        return httpx.Response(case["response"].get("http_status", 200), content=body)

    async with AsyncBpiClient(
        transport=httpx.MockTransport(handler),
        clock=lambda: NOW,
        cookie="SESSDATA=test-session; bili_jct=test-csrf" if authenticated else None,
    ) as client:
        method = getattr(getattr(client, recipe["domain"]), recipe["method"])
        if response_case.get("http_status", 200) >= 400:
            with pytest.raises(HttpStatusError) as error:
                await method(**recipe["kwargs"])
            assert error.value.status_code == response_case["http_status"]
        elif case["response"]["api_code"]:
            with pytest.raises(ApiError) as error:
                await method(**recipe["kwargs"])
            assert error.value.code == case["response"]["api_code"]
            if response_case.get("error") == "requires_login":
                assert error.value.requires_login()
        else:
            value = await method(**recipe["kwargs"])
            expected = json.loads(body).get("data", json.loads(body).get("result"))
            if value is None:
                assert expected is None
            elif type(value) in (str, int, bool):
                assert type(value) is type(expected)
                assert value == expected
            elif isinstance(value, list):
                assert len(value) == len(expected)
            elif recipe["contract"] == "bangumi.info.review_user":
                assert value.media.title == expected["media"]["title"]
            else:
                assert value.model_dump()
    assert len(calls) == (2 if recipe["signed"] else 1)


@pytest.mark.parametrize(
    "domain,method,kwargs",
    [
        ("video", "tags", {"aid": 2, "cid": True}),
        ("video", "online_total", {"aid": 2, "cid": 0}),
        ("video", "ai_summary", {"aid": 2, "cid": 1, "up_mid": 0}),
        ("video", "desc", {"aid": 2, "bvid": "BV1xx411c7mD"}),
        ("bangumi", "info", {"media_id": True}),
        ("bangumi", "timeline", {"types": 2, "before": 3, "after": 7}),
        ("bangumi", "timeline", {"types": 1, "before": -1, "after": 7}),
        ("bangumi", "timeline", {"types": 1, "before": 3, "after": 8}),
    ],
)
async def test_invalid_parameters_fail_before_network(domain, method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(getattr(client, domain), method)(**kwargs)


async def test_tags_can_omit_cid_and_use_aid():
    def handler(request):
        assert dict(request.url.params) == {"aid": "2"}
        return httpx.Response(200, json={"code": 0, "data": []})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        assert await client.video.tags(aid=2) == []


def test_bangumi_missing_rating_uses_reviewed_rust_default():
    contract_path = FIXTURES / "bangumi/info/review-user/contract.json"
    contract = json.loads(contract_path.read_bytes())
    body = json.loads(
        (contract_path.parent / contract["cases"][0]["response"]["fixture"]).read_bytes()
    )
    payload = body.get("result", body.get("data"))
    payload["media"].pop("rating", None)
    model = BangumiInfoResult.model_validate(payload)
    assert model.media.rating.count == 0 and model.media.rating.score == 0.0


def test_tags_resolves_the_correct_same_named_type():
    tag = VideoTag.model_validate({"tag_name": "music", "tag_type": "bgm", "music_id": "123"})
    assert tag.tag_id is None and tag.music_id == "123"
    with pytest.raises(ValidationError):
        VideoTag.model_validate({"tag_id": 1, "tag_name": "wrong-model-without-tag-type"})


async def test_generated_payload_drift_preserves_same_response():
    body = b'{"code":0,"data":{"following":"private-marker","follower":1,"dynamic_count":1}}'
    async with AsyncBpiClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    ) as client:
        with pytest.raises(ResponseDecodeError) as error:
            await client.login.stat()
    assert error.value.response_body == body
    assert "private-marker" not in str(error.value)


def test_fixture_hashes():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    for path, digest in provenance["sha256"].items():
        assert hashlib.sha256((FIXTURES / path).read_bytes()).hexdigest() == digest
