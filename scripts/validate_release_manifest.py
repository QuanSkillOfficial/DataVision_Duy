"""Validate a Week 8 release manifest and expose immutable image references."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


FULL_SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
SERVICES = ("backend", "ui", "seed")


def load_and_validate(
    manifest_path: Path,
    *,
    expected_sha: str,
    image_prefix: str,
    expected_ci_run_id: int | None = None,
) -> tuple[dict[str, object], dict[str, str]]:
    if not FULL_SHA.fullmatch(expected_sha):
        raise ValueError("expected SHA must be a full lowercase Git SHA")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("release manifest schema_version must be 1")
    if manifest.get("release_sha") != expected_sha:
        raise ValueError("release manifest SHA does not match requested release")
    if not isinstance(manifest.get("source_ci_run_id"), int):
        raise ValueError("release manifest source_ci_run_id is required")
    if expected_ci_run_id is not None and manifest["source_ci_run_id"] != expected_ci_run_id:
        raise ValueError("release manifest is not bound to the verified CI run")
    images = manifest.get("images")
    if not isinstance(images, dict) or set(images) != set(SERVICES):
        raise ValueError("release manifest must contain exactly backend, ui, and seed")

    normalized_prefix = image_prefix.lower().rstrip("/")
    refs: dict[str, str] = {}
    for service in SERVICES:
        entry = images[service]
        if not isinstance(entry, dict):
            raise ValueError(f"{service} image entry must be an object")
        repository = f"{normalized_prefix}-{service}"
        tag = f"{repository}:{expected_sha}"
        digest = entry.get("digest")
        ref = f"{repository}@{digest}"
        if entry.get("repository") != repository:
            raise ValueError(f"{service} repository is not canonical")
        if entry.get("tag") != tag:
            raise ValueError(f"{service} tag is not bound to the release SHA")
        if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
            raise ValueError(f"{service} digest is malformed")
        if entry.get("ref") != ref:
            raise ValueError(f"{service} immutable ref does not match repository and digest")
        refs[service] = ref
    return manifest, refs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--image-prefix", required=True)
    parser.add_argument("--expected-ci-run-id", type=int)
    parser.add_argument("--github-env")
    args = parser.parse_args()

    manifest, refs = load_and_validate(
        args.manifest,
        expected_sha=args.expected_sha,
        image_prefix=args.image_prefix,
        expected_ci_run_id=args.expected_ci_run_id,
    )
    manifest_sha256 = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
    if args.github_env:
        with open(args.github_env, "a", encoding="utf-8") as handle:
            handle.write(f"BACKEND_IMAGE_REF={refs['backend']}\n")
            handle.write(f"UI_IMAGE_REF={refs['ui']}\n")
            handle.write(f"SEED_IMAGE_REF={refs['seed']}\n")
            handle.write(f"RELEASE_MANIFEST_SHA256={manifest_sha256}\n")
    print(
        json.dumps(
            {
                "status": "passed",
                "release_sha": manifest["release_sha"],
                "source_ci_run_id": manifest["source_ci_run_id"],
                "manifest_sha256": manifest_sha256,
                "images": refs,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
