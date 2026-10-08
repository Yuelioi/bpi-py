"""公共播放流的缺省画质字段与 Rust 0.3.1 一致。"""

import json
from pathlib import Path

import pytest

from bpi.bangumi.models import BangumiVideoStreamData
from bpi.video.models import PlayUrlResponseData

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "model,fixture,envelope_key",
    [
        (
            PlayUrlResponseData,
            "tests/sdk/fixtures/video/playurl/play-url/responses/success.json",
            "data",
        ),
        (
            BangumiVideoStreamData,
            "tests/generated_reads/fixtures/bangumi/playurl/responses/anonymous.success.json",
            "result",
        ),
    ],
)
def test_missing_accept_fields_preserve_playback_payload(model, fixture, envelope_key):
    envelope = json.loads((ROOT / fixture).read_bytes())
    payload = envelope[envelope_key]
    original = model.model_validate(payload)
    for field in ("accept_quality", "accept_format", "accept_description"):
        payload.pop(field, None)
    value = model.model_validate(payload)
    assert value.accept_quality == []
    assert value.accept_description == []
    assert value.accept_format == ""
    assert value.quality == original.quality
    assert value.dash == original.dash
    assert value.durl == original.durl
