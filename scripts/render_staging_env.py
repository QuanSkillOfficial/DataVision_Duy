"""Render the remote Compose environment without printing staging secrets."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
from pathlib import Path
from urllib.parse import quote

from validate_release_manifest import load_and_validate


FULL_SHA = re.compile(r"[0-9a-f]{40}")


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def compose_value(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def allowed_cidrs() -> str:
    """Return a validated, fail-closed reviewer allowlist.

    The two private ranges are added for traffic arriving through the SSH
    acceptance tunnel and Docker's bridge. Basic authentication still applies
    to those requests; the public reviewer ranges remain explicitly managed by
    the staging Environment.
    """

    configured = required("STAGING_ALLOWED_CIDRS").split()
    networks: list[str] = []
    for value in configured:
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError as exc:
            raise ValueError(f"Invalid STAGING_ALLOWED_CIDRS entry: {value}") from exc
        if network.prefixlen == 0:
            raise ValueError("STAGING_ALLOWED_CIDRS must not allow the whole Internet")
        networks.append(str(network))

    for internal in ("127.0.0.1/32", "172.16.0.0/12"):
        if internal not in networks:
            networks.append(internal)
    return " ".join(networks)


def render(output: Path, manifest_path: Path) -> None:
    release_sha = required("RELEASE_SHA").lower()
    if not FULL_SHA.fullmatch(release_sha):
        raise ValueError("RELEASE_SHA must be a full 40-character lowercase Git SHA")

    image_prefix = required("IMAGE_PREFIX").lower().rstrip("/")
    if not image_prefix.startswith("ghcr.io/"):
        raise ValueError("IMAGE_PREFIX must point to ghcr.io")

    _, image_refs = load_and_validate(
        manifest_path,
        expected_sha=release_sha,
        image_prefix=image_prefix,
    )

    user = os.getenv("POSTGRES_USER", "datavision")
    password = required("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB", "datavision_db")
    database_url = (
        f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}"
        f"@db:5432/{quote(database, safe='')}"
    )
    values = {
        "COMPOSE_PROJECT_NAME": os.getenv("COMPOSE_PROJECT_NAME", "datavision-staging"),
        "DATAVISION_RELEASE_SHA": release_sha,
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": database,
        "DATABASE_URL": database_url,
        "RAG_EMBEDDING_MODE": os.getenv("RAG_EMBEDDING_MODE", "hash"),
        "BACKEND_PUBLIC_PORT": os.getenv("BACKEND_PUBLIC_PORT", "8000"),
        "UI_PUBLIC_PORT": os.getenv("UI_PUBLIC_PORT", "8501"),
        "STAGING_ALLOWED_CIDRS": allowed_cidrs(),
        "QS_RELEASE_SHA": release_sha,
        "QS_ENVIRONMENT": "staging",
        "QS_IMAGE_DIGEST": image_refs["ui"].split("@", 1)[1],
        "BACKEND_IMAGE": image_refs["backend"],
        "UI_IMAGE": image_refs["ui"],
        "SEED_IMAGE": image_refs["seed"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(f"{key}={compose_value(value)}" for key, value in values.items()) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    render(Path(args.output), args.manifest)
    print(f"Rendered staging environment at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
