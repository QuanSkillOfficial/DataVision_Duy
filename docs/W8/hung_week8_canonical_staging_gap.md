# Week 8 — Canonical Cloud Staging: UI Findings and Required Changes

**Owner:** Hưng (Streamlit UI, backend contracts, user journey)
**Tasks:** DV-HUNG-04, DV-HUNG-06, DV-HUNG-07
**Reviewed:** `QuanSkillOfficial/DataVision_Duy` @ `ca19091095809047a143536186bd76d03f728449` (default branch `main`)
**Date:** 17 August 2026

---

## 1. What changed since the completion review

`WEEK8_FINAL_TASK_COMPLETION_REVIEW.md` recorded `Private staging deployment runs: 0`
and treated DV-HUNG-06 as blocked on a staging host that did not exist. That is no
longer the whole picture. Canonical `main` already carries a complete cloud staging
delivery pipeline, merged as PR #2:

| Artifact | Purpose |
|---|---|
| `.github/workflows/release-staging-images.yml` | Publishes backend, UI and seed images per SHA |
| `.github/workflows/deploy-staging.yml` | `workflow_dispatch` deploy over SSH, with rollback |
| `deployment/cloud/docker-compose.staging.yml` | The deployed stack |
| `scripts/week8_remote_staging_smoke_test.py` | 15-check cloud acceptance bound to an expected SHA |

So DV-HUNG-06 is no longer blocked on *building* a staging environment. It is blocked
on three concrete defects, below. Two are in canonical, one was on the UI side and is
fixed by this change.

---

## 2. Finding 1 — P0: staging publishes an unauthenticated Streamlit endpoint

`deployment/cloud/docker-compose.staging.yml` publishes the UI straight onto the host:

```yaml
  ui:
    image: ${UI_IMAGE:?UI_IMAGE is required}
    ports:
      - "${UI_PUBLIC_PORT:-8501}:8501"
```

There is no proxy, no authentication and no network restriction anywhere in the
canonical deployment path. `deploy-staging.yml` declares that address as the
`ui_url` input — "Public Streamlit URL" — and publishes it as the URL of the
`staging` GitHub Environment.

Streamlit has no authentication of its own. Anyone who reaches that host and port
can read every uploaded document and its extracted text, run predictions, see the
review queue, ask RAG questions over indexed content, and download generated
reports.

This is a direct failure of two accepted criteria:

- DV-HUNG-07 acceptance: *the absence of an unauthenticated public Streamlit endpoint*;
- Final release criteria §13: *private staging access is protected*.

**Impact on the release:** staging must not be deployed, and no staging URL should
be shared, until the controls below are in place. If the pipeline has already been
dispatched against a reachable host, treat any data loaded there as disclosed.

### Remedy delivered

`deployment/cloud/docker-compose.staging-proxy.yml` (new, in this repository) layers
an authenticating reverse proxy over the canonical stack. It reuses the two files
DV-HUNG-07 already ships, `deployment/staging/nginx-staging-ui.conf` and
`deployment/staging/render-allowlist.sh`, so there is one implementation of the
controls, not two.

Design points that matter for review:

- The proxy takes over **the same published port** the UI used, so `ui_url`, the
  GitHub Environment URL and the 15-check acceptance keep working unchanged.
- The UI keeps no host port at all (`ports: !reset []`), so it is reachable only
  through the proxy.
- Two independent controls apply: an IP allowlist rendered from
  `STAGING_ALLOWED_CIDRS`, and HTTP basic auth against a mounted `htpasswd`.
- The proxy **refuses to start** when `STAGING_ALLOWED_CIDRS` is unset or empty, so
  a misconfigured deployment fails loudly instead of coming up open.
- `GET /_stcore/health` is exempt from both controls, by exact path match only. The
  canonical acceptance check calls it from a GitHub-hosted runner whose address
  cannot be allowlisted, and it returns a fixed `ok` carrying no application data.
  The rest of the `/_stcore/` namespace — the websocket and the upload endpoint —
  stays behind both controls.

Verified with `docker compose config` against the real canonical compose file in a
bundle laid out exactly as `deploy-staging.yml` builds it:

```text
backend        published=['8000->8000']
db             published=none
staging-seed   published=none
ui             published=none          <- was 8501->8501
ui-proxy       published=['8501->8080']
```

### Changes still required in canonical (owner: Duy)

1. **Bundle step** — `deploy-staging.yml`, "Build secret-safe deployment bundle":

   ```bash
   cp deployment/cloud/docker-compose.staging.yml staging-bundle/
   cp deployment/cloud/docker-compose.staging-proxy.yml staging-bundle/
   cp deployment/staging/nginx-staging-ui.conf staging-bundle/
   cp deployment/staging/render-allowlist.sh staging-bundle/
   printf '%s\n' "$STAGING_UI_HTPASSWD" > staging-bundle/htpasswd
   ```

   and add both `-f` files to the `config --quiet` validation, then
   `chmod 600 staging-bundle/htpasswd` alongside the existing `.env.staging` chmod.

2. **Deploy step** — every `docker compose` invocation on the host must carry both
   overlays:

   ```bash
   docker compose --env-file .env.staging \
     -f docker-compose.staging.yml -f docker-compose.staging-proxy.yml pull
   docker compose --env-file .env.staging \
     -f docker-compose.staging.yml -f docker-compose.staging-proxy.yml up -d
   ```

   The rollback step needs the same treatment, or a rollback would restore an
   unprotected UI.

3. **Configuration** — add to the `staging` Environment:
   `vars.STAGING_ALLOWED_CIDRS` (approved reviewer networks, space separated) and
   `secrets.STAGING_UI_HTPASSWD` (output of
   `bash deployment/staging/generate_htpasswd.sh reviewer`).

4. **Rendered env** — `scripts/render_staging_env.py` must emit
   `STAGING_ALLOWED_CIDRS` into `.env.staging`, since the host runs compose with
   `--env-file .env.staging`.

5. **TLS** — basic-auth credentials cross the network in clear text until TLS
   terminates in front of the proxy. This remains open and is the last control
   needed before any URL is shared.

---

## 3. Finding 2 — release identity was invisible on canonical staging

The canonical stack injects `DATAVISION_RELEASE_SHA` into every service, and the
backend reports it through `/api/health`:

```python
# backend_stub/runtime.py
"release_sha": os.getenv("DATAVISION_RELEASE_SHA", "local"),
```

The UI read `QS_RELEASE_SHA` only. `QS_RELEASE_SHA`, `QS_IMAGE_DIGEST` and
`QS_ENVIRONMENT` appear nowhere in canonical. A UI deployed by this pipeline would
therefore have reported `release_sha: unknown` and `release_match: unknown` — so
DV-HUNG-04 could not be verified on the one environment it exists to describe, and
the DV-HUNG-06 acceptance rule "UI and backend report the same release SHA" could
never have evaluated to `match`.

**Fixed on the UI side.** `demo/config.py` now falls back to
`DATAVISION_RELEASE_SHA` when `QS_RELEASE_SHA` is unset; a deployment-specific
`QS_RELEASE_SHA` still wins when both are present. Covered by two tests in
`tests/test_release_identity.py`.

Optional follow-up for canonical: also inject `QS_ENVIRONMENT: staging` and
`QS_IMAGE_DIGEST` into the `ui` service, so the header states the environment and
the exact digest rather than defaulting to `local` and `unknown`.

---

## 4. Finding 3 — cloud acceptance verifies the UI with a single liveness probe

`scripts/week8_staging_smoke_test.py` reduces the whole UI to one check:

```python
"ui_healthy": "ok" in ui_health.lower() and ui_backend_mode,
```

That is `GET {ui_url}/_stcore/health` plus a container-level assertion that
`QS_USE_BACKEND == "true"`. Streamlit answers that endpoint with `ok` even when
every page raises, so the 15-check acceptance can report a green UI for a release in
which no page renders. This is the same class of false green that Week 8 was opened
to remove — moved from fixture mode to deployment.

DV-HUNG-06 exists to close it: the browser journey asserts the real pages, the real
release identity, and real citations against the deployed services. It should run as
a required step in `deploy-staging.yml` after the acceptance check, not as a manual
afterthought.

---

## 5. Finding 4 — canonical's generated UI fixtures violate the UI contract

The Tường prediction fixtures on canonical `main` carry null identifiers:

```text
demo/fixtures/week7/tuong_prediction_batch_response.json
    document_external_id: null

demo/fixtures/week7/tuong_prediction_review_queue_sample.json
    review_items[].prediction_log_id: null
```

`demo/services/fixture_validator.py` treats `document_external_id` as a required
non-null field, and `tests/test_week7_fixture_validation.py` requires
`prediction_log_id`. Both exist so a reviewer can trace a prediction back to the
document it classified and to its log row; a null breaks that chain, which is the
traceability the Week 8 release criteria are built on.

Verified on the integration branch: with canonical's fixtures the UI validation
fails three tests, and with the UI's own fixtures it passes seven. Both sets keep
`tests/ai_tests/test_ui_fixtures.py` green (18 passed), so the integration branch
carries the UI's contract-conformant fixtures.

**This is not closed by that choice.** `scripts/week7_refresh_fixtures.py`
regenerates these files, so the next refresh reintroduces the nulls. The fix
belongs upstream, in the payloads Tường produces or in the generator that maps
them — owner: Tường, related to DV-TUONG-02 and DV-TUONG-06. Until then, a
regenerated fixture set will fail the UI gate.

---

## 6. UI-side changes delivered in this repository

| Change | Task | Why |
|---|---|---|
| `demo/config.py` reads `DATAVISION_RELEASE_SHA` as a fallback | DV-HUNG-04 | Release identity works under the canonical pipeline (Finding 2) |
| `deployment/cloud/docker-compose.staging-proxy.yml` | DV-HUNG-07 | Closes the unauthenticated endpoint (Finding 1) |
| `/_stcore/health` exemption in `nginx-staging-ui.conf` | DV-HUNG-07 | Keeps canonical's acceptance check working behind the controls |
| `staging` pytest marker; `-m "e2e and staging"` in external mode | DV-HUNG-06 | Only tests that can describe a deployed UI run against one |
| `QS_E2E_HTTP_USER` / `QS_E2E_HTTP_PASSWORD` on the browser context | DV-HUNG-06 | URL-embedded credentials are not sent on Streamlit's websocket and XHR calls, so the app would 401 after the first page |
| `unreachable_backend_app_url` fails loudly in external mode | DV-HUNG-06 | It starts its own local UI; silently testing localhost would file a local pass as staging evidence |
| `STAGING_EXCLUSIONS` recorded in the evidence file | DV-HUNG-06 | Excluded tests are declared with a reason, never silently skipped |

---

## 7. Status after this change

| Task | State | Remaining |
|---|---|---|
| DV-HUNG-04 | Ready | Verify in the deployed UI header once staging runs |
| DV-HUNG-06 | Unblocked, not executed | Needs the canonical changes in §2 merged, then one run of `week8_run_browser_e2e.py --base-url <ui_url> --release-sha <sha>` from an allowlisted machine |
| DV-HUNG-07 | Implemented for cloud, not deployed | Needs §2 items 1–4 merged and TLS (item 5) |

**Blocking for the whole team:** do not dispatch `deploy-staging.yml`, and do not
share a staging URL, until §2 items 1–4 are merged. The current canonical path
deploys an open UI.

The staging acceptance run itself is unchanged from
`hung_week8_staging_access_and_browser_validation.md` §4–5, except that the browser
run now needs `QS_E2E_HTTP_USER` and `QS_E2E_HTTP_PASSWORD` in the environment and
must be executed from a network inside `STAGING_ALLOWED_CIDRS`.
