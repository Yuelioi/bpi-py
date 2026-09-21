from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.migration.inventory import build_inventory, render_report
from tools.migration.rust import extract_file


def write(root: Path, name: str, content: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def contract(root: Path, name: str = "video.view", url: str = "https://example.test/view") -> Path:
    return write(
        root,
        f"tests/contracts/{name}/contract.json",
        json.dumps(
            {
                "schema_version": 2,
                "name": name,
                "module": name.split(".")[0],
                "risk": "public-read",
                "status": "promoted",
                "request": {"method": "GET", "url": url, "query": {}, "auth": {"requires": []}},
                "cases": [{"name": "success", "response": {"fixture": "responses/success.json"}}],
            }
        ),
    )


@pytest.fixture
def source(tmp_path: Path) -> Path:
    write(tmp_path, "Cargo.toml", '[package]\nname="sample"\n[features]\nfull=["video", "user"]')
    contract(tmp_path)
    write(tmp_path, "tests/contracts/video.view/responses/success.json", '{"code":0,"data":{}}')
    write(
        tmp_path,
        "src/video/client.rs",
        """
const ENDPOINT: &str = "https://example.test/view";
impl VideoClient<'_> {
    pub async fn view(&self, params: Params) -> BpiResult<View> {
        self.client.get(ENDPOINT).query(&params.query_pairs())
            .send_bpi_payload("video.view").await
    }
}
""",
    )
    return tmp_path


def test_ast_ignores_comments_tests_and_restricted_visibility(source: Path) -> None:
    path = write(
        source,
        "src/video/other.rs",
        """
// pub async fn fake() { client.get("https://wrong"); }
#[cfg(test)]
mod fixture {
    pub async fn hidden() {}
}
impl VideoClient {
    #[cfg(test)]
    pub async fn hidden_method() {}
    pub(crate) async fn internal() {}
    pub async fn visible(&self) -> Result<Vec<Pair<A, B>>, Error> {
        let note = "pub async fn phantom() {}";
        pub async fn nested() {}
    }
}
""",
    )
    result = extract_file(path, source, {"video"})
    assert [m["name"] for m in result["methods"]] == ["visible"]
    assert result["methods"][0]["return_type"] == "Result<Vec<Pair<A, B>>, Error>"


def test_exact_label_and_parameter_evidence(source: Path) -> None:
    result = build_inventory(source)
    method = result["methods"][0]
    assert method["contracts"] == [{"contract": "video.view", "evidence": "contract_label"}]
    assert method["parameter_bindings"] == [
        {"location": "query", "expression": "&params.query_pairs()"}
    ]
    assert method["automation"] == "request_shell_candidate"
    assert method["migration_status"] == "not_generated"


def test_same_named_endpoint_in_other_domain_cannot_match(source: Path) -> None:
    write(
        source,
        "src/user/client.rs",
        """
const ENDPOINT: &str = "https://example.test/view";
impl UserClient {
    pub async fn view(&self) { self.client.get(ENDPOINT).send_bpi_payload("video.view").await }
}
""",
    )
    result = build_inventory(source)
    user = next(m for m in result["methods"] if m["domain"] == "user")
    assert user["contracts"] == []
    assert result["contracts"][0]["mapping"] == "label_unique"


def test_url_candidates_do_not_claim_exact_mapping(source: Path) -> None:
    path = source / "src/video/client.rs"
    path.write_text(path.read_text().replace('"video.view"', '"other.label"'))
    result = build_inventory(source)
    assert result["contracts"][0]["mapping"] == "url_candidate"
    assert result["methods"][0]["automation"] == "manual_review"


def test_reused_label_and_conflicting_request_require_review(source: Path) -> None:
    write(
        source,
        "src/video/duplicate.rs",
        """
impl VideoClient {
    pub async fn other(&self) {
        self.client.post("https://example.test/other").send_bpi_payload("video.view").await
    }
}
""",
    )
    result = build_inventory(source)
    assert result["contracts"][0]["mapping"] == "label_ambiguous"
    assert all(m["automation"] == "manual_review" for m in result["methods"])
    other = next(m for m in result["methods"] if m["name"] == "other")
    assert "label_request_mismatch" in other["review_reasons"]


def test_unknown_helper_stays_visible_without_guessing(source: Path) -> None:
    write(
        source,
        "src/video/helper.rs",
        """
impl VideoClient {
    pub async fn delegated(&self, params: Params) -> BpiResult<View> {
        self.fetch_typed(params, "video.custom").await
    }
}
""",
    )
    result = build_inventory(source)
    method = next(m for m in result["methods"] if m["name"] == "delegated")
    assert method["contracts"] == []
    assert "indirect_or_multiple_requests" in method["review_reasons"]
    assert "fetch_typed" in method["calls"]


def test_flow_contract_keeps_steps(source: Path) -> None:
    write(
        source,
        "tests/contracts/flow/contract.json",
        json.dumps(
            {
                "name": "video.flow",
                "module": "video",
                "risk": "login-session",
                "steps": [
                    {
                        "name": "generate",
                        "contract": {
                            "name": "generate",
                            "request": {"method": "GET", "url": "https://example.test/view"},
                        },
                        "extract": {"key": "/data/key"},
                    }
                ],
            }
        ),
    )
    result = build_inventory(source)
    flow = next(c for c in result["contracts"] if c["id"] == "video.flow")
    assert flow["mapping"] == "flow_review"
    assert flow["steps"][0]["extract"] == {"key": "/data/key"}


def test_model_keeps_serde_metadata_and_private_fields(source: Path) -> None:
    path = write(
        source,
        "src/video/models.rs",
        """
#[derive(Deserialize)]
pub struct View {
    #[serde(rename = "isLogin", default)]
    pub is_login: bool,
    private: Option<Vec<String>>,
}
""",
    )
    model = extract_file(path, source, {"video"})["types"][0]
    assert model["fields"][0]["attributes"] == ['#[serde(rename = "isLogin", default)]']
    assert model["fields"][1]["rust_type"] == "Option<Vec<String>>"


def test_bad_rust_fails_instead_of_silently_omitting_methods(source: Path) -> None:
    write(source, "src/video/broken.rs", "impl Broken { pub async fn broken( {")
    with pytest.raises(ValueError, match="Rust syntax error"):
        build_inventory(source)


def test_missing_fixture_fails(source: Path) -> None:
    contract(source, "video.missing")
    with pytest.raises(ValueError, match="Missing fixture"):
        build_inventory(source)


def test_escaping_fixture_is_rejected(source: Path) -> None:
    path = source / "tests/contracts/video.view/contract.json"
    data = json.loads(path.read_text())
    data["cases"][0]["response"]["fixture"] = "../../../../../outside.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="escapes source root"):
        build_inventory(source)


def test_output_is_repeatable_and_fingerprints_content_changes(source: Path) -> None:
    first = build_inventory(source)
    second = build_inventory(source)
    assert first == second
    assert render_report(first) == render_report(second)
    fixture = source / "tests/contracts/video.view/responses/success.json"
    fixture.write_text('{"code":0,"data":{"new":1}}')
    assert build_inventory(source)["baseline"]["input_sha256"] != first["baseline"]["input_sha256"]


def test_duplicate_contract_id_is_rejected(source: Path) -> None:
    content = (source / "tests/contracts/video.view/contract.json").read_text()
    write(source, "tests/contracts/duplicate/contract.json", content)
    write(source, "tests/contracts/duplicate/responses/success.json", "{}")
    with pytest.raises(ValueError, match="Duplicate contract ID"):
        build_inventory(source)


def test_ambiguous_constant_is_not_a_template_candidate(source: Path) -> None:
    path = source / "src/video/client.rs"
    path.write_text(
        path.read_text().replace('const ENDPOINT: &str = "https://example.test/view";', "")
    )
    write(source, "src/video/a.rs", 'const ENDPOINT: &str = "https://example.test/view";')
    write(source, "src/video/b.rs", 'const ENDPOINT: &str = "https://example.test/other";')
    method = build_inventory(source)["methods"][0]
    assert "ambiguous_url" in method["review_reasons"]
    assert method["automation"] == "manual_review"
