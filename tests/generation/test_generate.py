from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.migration.generate import HEADER, ModelEmitter, load_spec, render, write_outputs

ROOT = Path(__file__).resolve().parents[2]


def inputs():
    return (
        json.loads((ROOT / "migration/generated/inventory.json").read_bytes()),
        load_spec(ROOT),
    )


def test_fixed_and_copied_queries_require_reviewed_values():
    inventory, spec = inputs()
    endpoint = next(e for e in spec["endpoints"] if e["method"] == "homepage_recommendations")
    endpoint["fixed_query"] = {"fresh_type": 4}
    with pytest.raises(ValueError, match="Fixed query"):
        render(inventory, spec)
    endpoint["fixed_query"] = {"fresh_type": "4"}
    endpoint["query_copies"] = {"brush": "unknown"}
    with pytest.raises(ValueError, match="Query copy"):
        render(inventory, spec)


def test_real_outputs_are_current_and_deterministic():
    inventory, spec = inputs()
    first = render(inventory, spec)
    assert render(inventory, spec) == first
    write_outputs(ROOT, first, check=True)


def test_unknown_type_is_not_replaced_with_any():
    inventory, _ = inputs()
    with pytest.raises(ValueError, match="unsupported type"):
        ModelEmitter(inventory, "video", {}).convert("UnknownModel", "src/video/tags.rs")


def test_ambiguous_name_requires_source_path():
    inventory, _ = inputs()
    emitter = ModelEmitter(inventory, "video", {})
    with pytest.raises(ValueError, match="Ambiguous"):
        emitter.convert("VideoTag", "unknown.rs")
    emitter.convert("VideoTag", "src/video/tags.rs")
    assert "music_id" in emitter.render()
    with pytest.raises(ValueError, match="collision"):
        emitter.convert("VideoTag", "src/video/model.rs")


def test_custom_serde_is_rejected():
    inventory, _ = inputs()
    with pytest.raises(ValueError, match="Unsupported serde"):
        ModelEmitter(inventory, "video", {}).convert("DashStream", "src/video/videostream_url.rs")


def test_nested_default_must_be_reviewed():
    inventory, _ = inputs()
    with pytest.raises(ValueError, match="Missing reviewed default"):
        ModelEmitter(inventory, "bangumi", {}).convert("BangumiInfoResult", "src/bangumi/info.rs")


def test_wrong_baseline_is_rejected():
    inventory, spec = inputs()
    spec["source_commit"] = "different"
    with pytest.raises(ValueError, match="commit"):
        render(inventory, spec)


def test_preflight_does_not_overwrite_handwritten_or_partially_write(tmp_path):
    handwritten = tmp_path / "handwritten.py"
    handwritten.write_text("important = True\n")
    with pytest.raises(ValueError, match="handwritten"):
        write_outputs(
            tmp_path, {"new.py": HEADER + "x = 1\n", "handwritten.py": HEADER}, check=False
        )
    assert not (tmp_path / "new.py").exists()
    assert handwritten.read_text() == "important = True\n"


def test_output_escape_and_stale_check_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        write_outputs(tmp_path, {"../outside.py": HEADER}, check=False)
    with pytest.raises(ValueError, match="differ"):
        write_outputs(tmp_path, {"generated.py": HEADER}, check=True)
    assert not (tmp_path / "generated.py").exists()


def test_non_get_request_fails_before_generation():
    inventory, spec = inputs()
    spec = copy.deepcopy(spec)
    spec["endpoints"] = [spec["endpoints"][0]]
    contract = next(
        c for c in inventory["contracts"] if c["id"] == spec["endpoints"][0]["contract"]
    )
    contract["request"]["method"] = "POST"
    with pytest.raises(ValueError, match="GET"):
        render(inventory, spec)


def test_external_reuse_and_scoped_rename_preserve_both_tag_types():
    inventory, spec = inputs()
    emitter = ModelEmitter(inventory, "video", {}, spec["model_names"], spec["external_models"])
    assert emitter.convert("VideoView", "src/video/model.rs") == "VideoView"
    assert "VideoView" not in emitter.emitted
    assert "from bpi.video.models import VideoView" in emitter.render()
    assert emitter.convert("VideoTag", "src/video/tags.rs") == "VideoTag"
    assert emitter.convert("VideoTag", "src/video/model.rs") == "VideoDetailTag"
    assert "music_id" in emitter.emitted["VideoTag"]
    assert "music_id" not in emitter.emitted["VideoDetailTag"]


def test_serde_alias_preserves_canonical_name():
    inventory, _ = inputs()
    emitter = ModelEmitter(inventory, "video", {})
    emitter.convert("PageInfo", "src/video/collection/info.rs")
    assert "AliasChoices('page_num', 'num')" in emitter.render()
    assert "AliasChoices('page_size', 'size')" in emitter.render()


def test_conflicting_batches_are_rejected(tmp_path):
    directory = tmp_path / "migration"
    directory.mkdir()
    for number, commit in ((3, "first"), (4, "second")):
        (directory / f"batch-{number}.json").write_text(
            json.dumps({"source_commit": commit, "endpoints": []})
        )
    with pytest.raises(ValueError, match="commits differ"):
        load_spec(tmp_path)


@pytest.mark.parametrize(
    "method,override,error",
    [
        ("info", {"host": "api.bilibili.com"}, "host"),
        ("info", {"host": "example.invalid"}, "host"),
        ("info", {"optional_payload": True}, "payload"),
        ("collection_info", {"optional_payload": False}, "payload"),
        ("collection_info", {"optional_payload": "yes"}, "boolean"),
        ("rank_period", {"csrf": None}, "CSRF"),
        ("rank_period", {"csrf": "required"}, "CSRF"),
        ("info", {"csrf": "optional"}, "CSRF"),
    ],
)
def test_audio_generation_rejects_unreviewed_request_modes(method, override, error):
    inventory, spec = inputs()
    endpoint = next(
        e for e in spec["endpoints"] if e["domain"] == "audio" and e["method"] == method
    )
    endpoint.update(override)
    spec["endpoints"] = [endpoint]
    with pytest.raises(ValueError, match=error):
        render(inventory, spec)


def test_map_conversion_preserves_nested_types_and_rejects_nonstring_keys():
    inventory, _ = inputs()
    emitter = ModelEmitter(inventory, "audio", {})
    assert (
        emitter.convert(
            "std::collections::HashMap<String, Vec<AudioRankPeriod>>", "src/audio/rank.rs"
        )
        == "dict[str, list[AudioRankPeriod]]"
    )
    assert "alias='ID'" in emitter.render()
    with pytest.raises(ValueError, match="unsupported type"):
        emitter.convert("std::collections::HashMap<u64, String>", "src/audio/rank.rs")


def test_struct_default_and_domain_external_type_are_explicit():
    inventory, spec = inputs()
    emitter = ModelEmitter(
        inventory,
        "bangumi",
        spec["model_defaults"],
        spec["model_names"],
        spec["external_models"],
        spec["external_types"],
    )
    emitter.convert("BangumiDetailResult", "src/bangumi/info.rs")
    rendered = emitter.render()
    assert "from bpi.bangumi.models import VipLabel" in rendered
    assert "favorite: int = Field(default=0)" in rendered
    assert "from_: str = Field(" in rendered and "alias='from'" in rendered
    assert "AliasChoices(" in rendered and "'coins'" in rendered and "'coin'" in rendered


def test_struct_default_requires_rust_default_derive():
    inventory, _ = inputs()
    inventory = copy.deepcopy(inventory)
    model = next(t for t in inventory["types"] if t["id"].endswith(":BangumiStat"))
    model["attributes"] = [a for a in model["attributes"] if "derive(" not in a]
    emitter = ModelEmitter(inventory, "bangumi", {})
    with pytest.raises(ValueError, match="requires a Default model"):
        emitter.convert("BangumiStat", "src/bangumi/info.rs")


def test_field_named_list_does_not_shadow_builtin_generic():
    inventory, spec = inputs()
    emitter = ModelEmitter(
        inventory,
        "user",
        spec["model_defaults"],
        spec["model_names"],
        spec["external_models"],
        spec["external_types"],
    )
    emitter.convert("UserFollowings", "src/user/model.rs")
    rendered = emitter.render()
    assert "import builtins" in rendered
    assert "list: builtins.list[UserFollowing]" in rendered


def test_top_level_external_response_is_imported_by_generated_client():
    inventory, spec = inputs()
    outputs = render(inventory, spec)
    client = outputs["src/bpi/_generated/user_client.py"]
    assert "from bpi.user.models import UserSpaceNotice, UserUpStat" in client
