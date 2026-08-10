"""Fail closed when required owner modules or recorded canonical trees drift."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


FULL_SHA = re.compile(r"[0-9a-f]{40}")
TREE_SHA = re.compile(r"[0-9a-f]{40}")
HTTPS_GITHUB_REPOSITORY = re.compile(
    r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?"
)


class ProvenanceError(ValueError):
    """Raised when provenance or canonical module parity is invalid."""


def _git(project_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        reason = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise ProvenanceError(reason)
    return completed.stdout.strip()


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceError(f"{field} must be a non-empty string")
    return value.strip()


def verify_manifest(project_root: Path, manifest_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"Cannot read provenance manifest: {exc}") from exc

    if payload.get("schema_version") != 1:
        raise ProvenanceError("Unsupported provenance schema_version")
    repository = _require_string(payload.get("canonical_repository"), "canonical_repository")
    if not HTTPS_GITHUB_REPOSITORY.fullmatch(repository):
        raise ProvenanceError("canonical_repository must be an HTTPS GitHub repository URL")
    baseline = _require_string(payload.get("canonical_baseline_sha"), "canonical_baseline_sha")
    import_commit = _require_string(payload.get("canonical_import_commit"), "canonical_import_commit")
    if not FULL_SHA.fullmatch(baseline) or not FULL_SHA.fullmatch(import_commit):
        raise ProvenanceError("Canonical commit identities must be full lowercase Git SHAs")
    _git(project_root, "cat-file", "-e", f"{baseline}^{{commit}}")
    _git(project_root, "cat-file", "-e", f"{import_commit}^{{commit}}")

    modules = payload.get("modules")
    if not isinstance(modules, list) or len(modules) != 5:
        raise ProvenanceError("Exactly five owner modules must be recorded")

    module_ids: set[str] = set()
    github_owners: set[str] = set()
    verified_paths: list[str] = []
    for index, module in enumerate(modules):
        if not isinstance(module, dict):
            raise ProvenanceError(f"modules[{index}] must be an object")
        prefix = f"modules[{index}]"
        module_id = _require_string(module.get("module_id"), f"{prefix}.module_id")
        if module_id in module_ids:
            raise ProvenanceError(f"Duplicate module_id: {module_id}")
        module_ids.add(module_id)
        owner = _require_string(module.get("owner_github"), f"{prefix}.owner_github")
        if owner in github_owners:
            raise ProvenanceError(f"Duplicate owner_github: {owner}")
        github_owners.add(owner)
        source_repository = _require_string(
            module.get("source_repository"), f"{prefix}.source_repository"
        )
        source_sha = _require_string(module.get("source_sha"), f"{prefix}.source_sha")
        if not HTTPS_GITHUB_REPOSITORY.fullmatch(source_repository):
            raise ProvenanceError(f"{module_id}: invalid source_repository")
        if not FULL_SHA.fullmatch(source_sha):
            raise ProvenanceError(f"{module_id}: source_sha must be a full lowercase Git SHA")

        canonical_paths = module.get("canonical_paths")
        if not isinstance(canonical_paths, list) or not canonical_paths:
            raise ProvenanceError(f"{module_id}: canonical_paths must not be empty")
        for path_entry in canonical_paths:
            if not isinstance(path_entry, dict):
                raise ProvenanceError(f"{module_id}: canonical path entry must be an object")
            relative_path = _require_string(path_entry.get("path"), f"{module_id}.path")
            expected_tree = _require_string(path_entry.get("tree_sha"), f"{module_id}.tree_sha")
            if Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
                raise ProvenanceError(f"{module_id}: unsafe canonical path {relative_path}")
            if not TREE_SHA.fullmatch(expected_tree):
                raise ProvenanceError(f"{module_id}: invalid canonical tree SHA")
            absolute_path = project_root / relative_path
            if not absolute_path.is_dir():
                raise ProvenanceError(f"{module_id}: canonical path is missing: {relative_path}")
            if (absolute_path / ".git").exists():
                raise ProvenanceError(f"{module_id}: nested Git repository is prohibited: {relative_path}")
            actual_tree = _git(project_root, "rev-parse", f"HEAD:{relative_path}")
            if actual_tree != expected_tree:
                raise ProvenanceError(
                    f"{module_id}: canonical tree drift for {relative_path}; "
                    "update code and provenance together"
                )
            verified_paths.append(relative_path)

        required_files = module.get("required_files")
        if not isinstance(required_files, list) or not required_files:
            raise ProvenanceError(f"{module_id}: required_files must not be empty")
        for relative_file in required_files:
            relative_file = _require_string(relative_file, f"{module_id}.required_file")
            if Path(relative_file).is_absolute() or ".." in Path(relative_file).parts:
                raise ProvenanceError(f"{module_id}: unsafe required file {relative_file}")
            if not (project_root / relative_file).is_file():
                raise ProvenanceError(f"{module_id}: required file is missing: {relative_file}")
            if not _git(project_root, "ls-files", "--error-unmatch", relative_file):
                raise ProvenanceError(f"{module_id}: required file is not tracked: {relative_file}")

    return {
        "status": "passed",
        "module_count": len(modules),
        "module_ids": sorted(module_ids),
        "canonical_paths": sorted(verified_paths),
        "baseline_sha": baseline,
        "canonical_import_commit": import_commit,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="integration/module_provenance.json",
        help="Repository-relative provenance manifest path",
    )
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    manifest_path = project_root / args.manifest
    try:
        result = verify_manifest(project_root, manifest_path)
    except ProvenanceError as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
