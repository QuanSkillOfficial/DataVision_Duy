# DataVision cloud staging

This directory is the immutable-image deployment contract for Week 8. The
server never builds application code. GitHub Actions publishes three images
tagged with a full green Git SHA and this Compose model pulls exactly those
tags.

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
2. `Publish staging images` builds backend, UI, and seed images, tags each one
   with the full commit SHA, pushes them to GHCR, and uploads a digest manifest.
3. Trigger `Deploy staging` with that full SHA, the public backend URL ending
   in `/api`, and the public UI URL.
4. The job pulls the exact tags, starts Compose over SSH, verifies backend mode
   and release identity, then runs the agreed 15 checks.
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
