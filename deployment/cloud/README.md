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
| `STAGING_UI_PASSWORD` | Basic-auth password for the staging reviewer account |

Environment variables (the first four have workflow defaults):

| Variable | Default |
| --- | --- |
| `STAGING_SSH_PORT` | `22` |
| `STAGING_PATH` | `/opt/datavision` |
| `STAGING_BACKEND_PORT` | `8000` |
| `STAGING_UI_PORT` | `8501` |
| `STAGING_UI_USER` | Required reviewer username, for example `reviewer` |
| `STAGING_ALLOWED_CIDRS` | Required space-separated reviewer networks; `/0` is rejected |

Do not create a secret by running `ssh-keyscan` inside the deployment job. The
host key must be verified out-of-band and stored as `STAGING_KNOWN_HOSTS`.
Where the GitHub plan supports it, add a required reviewer to the Environment.

## Release flow

1. `DataVision CI` passes on `main`.
2. `Publish staging images` first proves the full SHA is reachable from `main`
   and has a successful `DataVision CI` run. It then builds backend, UI, and seed
   images, pushes them to GHCR, scans the exact digests, creates SBOMs, and
   uploads a release manifest bound to the successful CI run.
3. Trigger `Deploy staging` with that full SHA and the HTTPS UI URL. Plain HTTP
   is rejected because reviewer credentials must never cross the network
   unencrypted. The backend is bound to host loopback and is tested through an
   SSH tunnel; it is not published as an unauthenticated Internet endpoint.
4. The job downloads and validates that manifest, runs a non-mutating remote
   preflight, creates an authenticated and allowlisted proxy, pulls the exact
   digests, starts Compose over SSH, verifies backend mode and release identity,
   then runs the agreed 15 checks.
5. It proves that the public runner is blocked by the IP allowlist, that missing
   credentials receive `401`, and that valid credentials work through an SSH
   acceptance tunnel. The full Playwright journey then exercises upload,
   dashboard, prediction, RAG/citations, suggestions, and report against the
   deployed stack.
6. Only after all API, access-control, and browser gates pass does the `current`
   symlink point to the new release. A failure re-applies only a previous
   protected release; it refuses to roll back to an unauthenticated UI.

The database volume is intentionally stable across releases and is never
removed by the workflow. Schema migrations must remain backward-compatible or
be paired with an explicit, separately approved database rollback procedure.

## Server prerequisites

- Ubuntu host with Docker Engine and Compose v2.
- The SSH user can run `docker` without an interactive prompt.
- Firewall/reverse proxy exposes only the chosen UI endpoint. The API port must
  remain loopback-only.
- Enough disk for the release directories, images, database, and backups.
- TLS termination must be configured in front of both endpoints before the
  workflow is dispatched; the deployment inputs accept HTTPS only.

## Manual rollback

Read the accepted target and list retained releases:

```bash
readlink /opt/datavision/current
ls -la /opt/datavision/releases
```

Then enter a previous protected release directory and re-apply its exact images:

```bash
cd /opt/datavision/releases/<previous-full-sha>
docker compose --env-file .env.staging \
  -f docker-compose.staging.yml \
  -f docker-compose.staging-proxy.yml up -d
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

Before mutating an existing release, the workflow creates a timestamped custom
format `pg_dump`, checks that it is non-empty, and validates it with
`pg_restore --list`. Schema migrations and idempotent seed execution remain
covered by Phat's owner and canonical CI gates.
