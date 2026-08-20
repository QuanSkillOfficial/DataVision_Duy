from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from validate_release_manifest import load_and_validate  # noqa: E402
from verify_release_candidate import select_green_run  # noqa: E402
from verify_module_provenance import ProvenanceError, _verify_codeowners  # noqa: E402


SHA = "a" * 40
PREFIX = "ghcr.io/quanskillofficial/datavision"


def write_manifest(path: Path, *, release_sha: str = SHA, ci_run_id: int = 123) -> Path:
    images = {}
    for index, service in enumerate(("backend", "ui", "seed"), start=1):
        repository = f"{PREFIX}-{service}"
        digest = f"sha256:{str(index) * 64}"
        images[service] = {
            "repository": repository,
            "tag": f"{repository}:{release_sha}",
            "digest": digest,
            "ref": f"{repository}@{digest}",
        }
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "release_sha": release_sha,
                "source_ci_run_id": ci_run_id,
                "images": images,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_manifest_accepts_exact_ci_bound_digest_refs(tmp_path: Path) -> None:
    manifest, refs = load_and_validate(
        write_manifest(tmp_path / "release.json"),
        expected_sha=SHA,
        image_prefix=PREFIX,
        expected_ci_run_id=123,
    )

    assert manifest["release_sha"] == SHA
    assert refs["backend"].startswith(f"{PREFIX}-backend@sha256:")
    assert all(":" not in ref.rsplit("@", 1)[0] for ref in refs.values())


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload.update(release_sha="b" * 40), "does not match"),
        (lambda payload: payload.update(source_ci_run_id=456), "verified CI run"),
        (
            lambda payload: payload["images"]["backend"].update(digest="sha256:short"),
            "digest is malformed",
        ),
        (
            lambda payload: payload["images"]["ui"].update(ref="ghcr.io/example/wrong"),
            "immutable ref",
        ),
    ],
)
def test_manifest_rejects_identity_drift(tmp_path: Path, mutation, message: str) -> None:
    path = write_manifest(tmp_path / "release.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutation(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_and_validate(
            path,
            expected_sha=SHA,
            image_prefix=PREFIX,
            expected_ci_run_id=123,
        )


def test_green_run_selection_requires_exact_main_sha_and_workflow() -> None:
    valid = {
        "id": 42,
        "head_sha": SHA,
        "head_branch": "main",
        "name": "DataVision CI",
        "status": "completed",
        "conclusion": "success",
        "html_url": "https://example.test/run/42",
    }
    newer_wrong_branch = {**valid, "id": 43, "head_branch": "feature"}

    selected = select_green_run(
        [newer_wrong_branch, valid],
        release_sha=SHA,
        branch="main",
        workflow_name="DataVision CI",
        expected_run_id=None,
    )

    assert selected["id"] == 42


def test_green_run_selection_rejects_failed_or_different_run() -> None:
    failed = {
        "id": 42,
        "head_sha": SHA,
        "head_branch": "main",
        "name": "DataVision CI",
        "status": "completed",
        "conclusion": "failure",
        "html_url": "https://example.test/run/42",
    }

    with pytest.raises(ValueError, match="no successful"):
        select_green_run(
            [failed],
            release_sha=SHA,
            branch="main",
            workflow_name="DataVision CI",
            expected_run_id=42,
        )


def test_codeowners_requires_each_module_owner_and_independent_governance_reviewer(
    tmp_path: Path,
) -> None:
    codeowners = tmp_path / ".github" / "CODEOWNERS"
    codeowners.parent.mkdir()
    codeowners.write_text(
        "\n".join(
            [
                "* @duy @reviewer",
                "/.github/ @duy @reviewer",
                "/integration/module_provenance.json @duy @phat @lap @tuong @hung",
                "/data_engineering/ @duy",
                "/week7/database/ @phat @duy",
                "/ai/rag/ @lap @duy",
                "/ai/prediction/ @tuong @duy",
                "/demo/ @hung @duy",
            ]
        ),
        encoding="utf-8",
    )
    modules = [
        {
            "module_id": module_id,
            "owner_github": owner,
            "canonical_paths": [{"path": path}],
        }
        for module_id, owner, path in (
            ("duy-ingestion", "duy", "data_engineering"),
            ("phat-database", "phat", "week7/database"),
            ("lap-rag", "lap", "ai/rag"),
            ("tuong-prediction", "tuong", "ai/prediction"),
            ("hung-ui", "hung", "demo"),
        )
    ]

    _verify_codeowners(tmp_path, modules)

    codeowners.write_text(
        codeowners.read_text(encoding="utf-8").replace("/.github/ @duy @reviewer", "/.github/ @duy"),
        encoding="utf-8",
    )
    with pytest.raises(ProvenanceError, match="independent Code Owner"):
        _verify_codeowners(tmp_path, modules)
