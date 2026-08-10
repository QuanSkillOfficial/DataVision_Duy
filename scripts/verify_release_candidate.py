"""Verify that a release SHA is an immutable, green commit on canonical main."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass


FULL_SHA = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class CandidateEvidence:
    release_sha: str
    main_ref: str
    workflow_name: str
    workflow_run_id: int
    workflow_url: str


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def verify_main_ancestry(release_sha: str, main_ref: str) -> None:
    if not FULL_SHA.fullmatch(release_sha):
        raise ValueError("release SHA must be 40 lowercase hexadecimal characters")
    git("cat-file", "-e", f"{release_sha}^{{commit}}")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", release_sha, main_ref],
        check=False,
    ).returncode != 0:
        raise ValueError(f"release SHA is not reachable from {main_ref}")


def github_json(url: str, token: str) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "datavision-release-governance",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def select_green_run(
    runs: list[dict[str, object]],
    *,
    release_sha: str,
    branch: str,
    workflow_name: str,
    expected_run_id: int | None,
) -> dict[str, object]:
    candidates = [
        run
        for run in runs
        if run.get("head_sha") == release_sha
        and run.get("head_branch") == branch
        and run.get("name") == workflow_name
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and (expected_run_id is None or run.get("id") == expected_run_id)
    ]
    if not candidates:
        qualifier = f" run {expected_run_id}" if expected_run_id is not None else ""
        raise ValueError(
            f"no successful {workflow_name}{qualifier} exists for {release_sha} on {branch}"
        )
    return sorted(candidates, key=lambda run: int(run["id"]), reverse=True)[0]


def verify_candidate(
    *,
    release_sha: str,
    main_ref: str,
    repository: str,
    token: str,
    branch: str,
    workflow_name: str,
    expected_run_id: int | None,
    api_url: str = "https://api.github.com",
) -> CandidateEvidence:
    verify_main_ancestry(release_sha, main_ref)
    query = urllib.parse.urlencode(
        {"branch": branch, "head_sha": release_sha, "status": "completed", "per_page": 100}
    )
    payload = github_json(f"{api_url}/repos/{repository}/actions/runs?{query}", token)
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        raise ValueError("GitHub Actions response did not contain workflow_runs")
    selected = select_green_run(
        runs,
        release_sha=release_sha,
        branch=branch,
        workflow_name=workflow_name,
        expected_run_id=expected_run_id,
    )
    return CandidateEvidence(
        release_sha=release_sha,
        main_ref=main_ref,
        workflow_name=workflow_name,
        workflow_run_id=int(selected["id"]),
        workflow_url=str(selected["html_url"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--workflow", default="DataVision CI")
    parser.add_argument("--expected-run-id", type=int)
    parser.add_argument("--github-env")
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("GITHUB_TOKEN is required")
    evidence = verify_candidate(
        release_sha=args.sha,
        main_ref=args.main_ref,
        repository=args.repository,
        token=token,
        branch=args.branch,
        workflow_name=args.workflow,
        expected_run_id=args.expected_run_id,
    )
    result = {
        "status": "passed",
        "release_sha": evidence.release_sha,
        "main_ref": evidence.main_ref,
        "workflow": evidence.workflow_name,
        "workflow_run_id": evidence.workflow_run_id,
        "workflow_url": evidence.workflow_url,
    }
    if args.github_env:
        with open(args.github_env, "a", encoding="utf-8") as handle:
            handle.write(f"VERIFIED_CI_RUN_ID={evidence.workflow_run_id}\n")
            handle.write(f"VERIFIED_CI_RUN_URL={evidence.workflow_url}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
