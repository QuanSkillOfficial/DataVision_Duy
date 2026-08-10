# DataVision cloud staging

This directory is the immutable-image deployment contract for Week 8. The
server never builds application code. GitHub Actions publishes three images
from a full green Git SHA, records their registry digests, and this Compose
model deploys only the manifest's `image@sha256` references.

## GitHub Environment

Create an Environment named `staging` and add these secrets:

| Secret | Purpose |
| --- | --- |
| `STAGING_HOST` | Public IP or DNS name of the Ubuntu host |
| `STAGING_USER` | SSH account that can run Docker |
| `STAGING_SSH_KEY` | Private SSH key for that account |
| `STAGING_KNOWN_HOSTS` | Pinned `known_hosts` line for the host |
| `POSTGRES_PASSWORD` | Staging-only PostgreSQL password |

Optional Environment variables:

| Variable | Default |
| --- | --- |
| `STAGING_SSH_PORT` | `22` |
| `STAGING_PATH` | `/opt/datavision` |
| `STAGING_BACKEND_PORT` | `8000` |
| `STAGING_UI_PORT` | `8501` |

Do not create a secret by running `ssh-keyscan` inside the deployment job. The
host key must be verified out-of-band and stored as `STAGING_KNOWN_HOSTS`.
Where the GitHub plan supports it, add a required reviewer to the Environment.

## Release flow

1. `DataVision CI` passes on `main`.
2. `Publish staging images` first proves the full SHA is reachable from `main`
   and has a successful `DataVision CI` run. It then builds backend, UI, and seed
   images, pushes them to GHCR, scans the exact digests, creates SBOMs, and
   uploads a release manifest bound to the successful CI run.
3. Trigger `Deploy staging` with that full SHA, the public backend URL ending
   in `/api`, and the public UI URL.
4. The job downloads and validates that manifest, runs a non-mutating remote
   preflight, pulls the exact digests, starts Compose over SSH, verifies backend
   mode and release identity, then runs the agreed 15 checks.
5. Only after acceptance passes does the `current` symlink point to the new
   release. A failure re-applies the previous accepted release if it exists.

The database volume is intentionally stable across releases and is never
removed by the workflow. Schema migrations must remain backward-compatible or
be paired with an explicit, separately approved database rollback procedure.

## Server prerequisites

- Ubuntu host with Docker Engine and Compose v2.
- The SSH user can run `docker` without an interactive prompt.
- Firewall/reverse proxy exposes the chosen UI and API endpoints.
- Enough disk for the release directories, images, database, and backups.
- TLS termination should be placed in front of public endpoints; complete TLS
  and authentication hardening remains a Week 9 gate.

## Manual rollback

Read the accepted target and list retained releases:

```bash
readlink /opt/datavision/current
ls -la /opt/datavision/releases
```

Then enter a previous release directory and re-apply its exact images:

```bash
cd /opt/datavision/releases/<previous-full-sha>
docker compose --env-file .env.staging -f docker-compose.staging.yml up -d
ln -sfn "$PWD" /opt/datavision/current
```

Run the cloud acceptance workflow again against the restored URLs. Do not use
`docker compose down --volumes` on staging.

## Fail-closed preflight and diagnostics

Before the workflow creates a release directory or uploads a bundle, it checks
Docker/Compose access, at least 2 GiB free disk space, path permissions, GHCR
DNS resolution, and current port ownership. A failed prerequisite stops before
deployment mutation and is retained in `remote-preflight.txt`. If a later step
fails, bounded Compose status and the last 200 log lines are uploaded as
`remote-failure-diagnostics.txt`.

The workflow does not back up or migrate a shared database by itself. The first
real staging deployment remains blocked until Phat's reviewed backup, restore,
migration, and idempotent-seed gates pass, and until the other owner P0 gates
listed in `docs/week8_repository_governance.md` are accepted.
