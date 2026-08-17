# Week 8 — Hưng Delivery Report (UI, Backend Contracts, Browser Journey)

**Owner:** Hưng
**Module:** Streamlit UI, backend contracts, user journey
**Repository:** `DataVision_Hung` (owner repository; canonical repository is `QuanSkillOfficial/DataVision_Duy`)
**Assigned tasks:** DV-HUNG-01 … DV-HUNG-07
**Report date:** 12 August 2026

---

## 1. Summary

Week 8 for this module was not feature work. The Week 8 review identified that
the UI's green results came from fixture-mode runs, which do not prove that the
UI works against a real backend. The work below closes that gap:

- backend-mode contract tests can no longer be skipped in a release candidate;
- the complete user journey is now verified in a real browser against a real
  backend, with screenshot evidence per step;
- the UI states which release and backend it is running against;
- backend failures produce actionable errors instead of tracebacks, and fixture
  data can no longer be displayed as if it were live.

Three real defects were found and fixed as a direct result, all of which were
invisible to the previous fixture-only test suite. They are listed in section 4.

**Status:** DV-HUNG-01 to DV-HUNG-05 are complete and verified locally.
DV-HUNG-06 and DV-HUNG-07 are implemented and locally verified but **cannot be
executed** until a private staging host exists (see section 6).

---

## 2. Task outcomes

| Task | Requirement | Status | Evidence |
|---|---|---|---|
| DV-HUNG-01 | No required UI-to-backend test is skipped in the release workflow | Complete | `outputs/week8/hung_backend_mode_gate.json`, CI job `ui-backend-mode-ci` |
| DV-HUNG-02 | Browser opens UI, verifies backend, runs prediction and RAG, validates citations, generates a report | Complete | `tests/e2e/test_user_journey.py`, `screenshots/week8_browser_e2e/00`–`06` |
| DV-HUNG-03 | Upload/ingestion, dashboard refresh, review queue and error handling against real services | Complete | Same journey plus `tests/e2e/test_error_handling.py`, screenshots `10`–`12` |
| DV-HUNG-04 | Reviewers can confirm which backend/release the UI is using | Complete | `demo/helpers/release_identity.py`, `tests/test_release_identity.py`, screenshot `00` |
| DV-HUNG-05 | Actionable timeout / partial-service / unavailable handling; no stale fixture success | Complete | `demo/services/service_errors.py`, `tests/test_service_error_contract.py`, screenshots `10`–`12` |
| DV-HUNG-06 | Browser test passes on the real private staging URL | **Ready, not executed** | `scripts/week8_staging_acceptance.py` is one command against a deployed URL; waiting on the staging URL, see §6 |
| DV-HUNG-07 | Authenticated proxy / VPN / IP allowlist before public sharing | **Implemented, not deployed** | `deployment/staging/`, `deployment/cloud/docker-compose.staging-proxy.yml`, runbook in `hung_week8_staging_access_and_browser_validation.md` |

### Correction to the status above

DV-HUNG-01 was reported Complete on the strength of a local run. It was not: the
gate collected `tests/e2e`, whose conftest imported Playwright from a
`pytest_configure` hook, so in the CI job that installs `requirements.txt` only,
collection aborted and **zero** of the 18 required contract tests ran. It passed
locally purely because Playwright happened to be installed. Fixed — the e2e setup
is a fixture that runs only when a browser test executes, and the gate selects the
UI test modules directly. The same hook also deleted the committed
`screenshots/week8_browser_e2e/` on any pytest run that touched `tests/e2e`.

DV-HUNG-04 was reported Complete but could not have been verified on a real
deployment: the canonical staging stack injects `DATAVISION_RELEASE_SHA`, the UI
read only `QS_RELEASE_SHA`, so a deployed UI would have reported an unknown
release. Fixed by a fallback in `demo/config.py`.

DV-HUNG-06 is no longer blocked on a host that does not exist. Canonical `main`
carries a cloud staging pipeline; it is blocked on the changes in
`hung_week8_canonical_staging_gap.md` §2, chiefly that the canonical stack
publishes Streamlit with no authentication at all.

---

## 3. What changed

### 3.1 DV-HUNG-01 — Backend-mode tests are mandatory

Before: `tests/test_backend_contract_smoke.py` skipped its entire module unless
`QS_USE_BACKEND=true`. A release run therefore reported "63 passed, 15 skipped"
while never once calling the backend.

Now:

- `QS_REQUIRE_BACKEND_TESTS=true` makes the module fail closed. If backend mode
  is not enabled, every backend test errors with an explicit message instead of
  skipping, and a dedicated guard test states the requirement.
- `scripts/week8_backend_mode_gate.py` starts the backend, runs the suite in
  backend mode, parses the JUnit report, and **fails on any skipped test**, on
  any failure, and when fewer than 15 UI-to-backend contract tests actually ran.
- CI job `ui-backend-mode-ci` runs the gate and uploads its evidence.

Two health/release-identity contract tests were added to the backend-mode
module, bringing it to 17 backend tests plus the guard.

### 3.2 DV-HUNG-02 / DV-HUNG-03 — Browser journey

`tests/e2e/` drives a real Chromium browser against a real Streamlit process in
backend mode, talking to a real HTTP backend:

```text
Release identity -> Upload/Ingestion -> Dashboard -> Prediction
-> Review status -> RAG -> Citations -> Suggestions -> Reports
```

It runs as **one continuous browser session**, navigating through the sidebar
rather than reloading URLs, because a reload starts a new Streamlit session and
would discard the state built up by the earlier steps. Eight isolated page
visits would not be a user journey.

The journey asserts, among other things, that the prediction card carries a
model version, that citations resolve to a chunk, page and document id, that
suggestions carry an evidence trace, and that the report renders a non-empty
evidence table. A `failed` prediction status fails the run.

### 3.3 DV-HUNG-04 — Release identity

The sidebar previously showed a hardcoded `Status: Online ✓ / Version 2.1.0 /
Users Online: 12`, which stayed green regardless of the actual system state and
was useless as release evidence.

It now shows resolved identity: environment, UI release SHA, data mode, backend
URL, backend release SHA and health latency, sourced from `QS_RELEASE_SHA`,
`QS_IMAGE_DIGEST`, `QS_ENVIRONMENT` and a live `GET /health` probe. When the UI
and backend report different SHAs, the UI warns that the session covers two
different builds.

The backend contract gained `GET /api/health` returning `ok`, `service`,
`release_sha` and `environment`.

### 3.4 DV-HUNG-05 — Failure handling

- Backend failures are classified as `timeout`, `unavailable`, `http_error` or
  `invalid_payload`, each with its own actionable next step, the failing
  endpoint and the elapsed time.
- Connect and read timeouts are now separate, so an unreachable host fails fast
  instead of waiting out a long read budget.
- Every page routes failures through a shared error block that names the service,
  says which part of the page cannot be shown, gives the next step, and exposes
  technical detail for the release evidence.
- Fixture mode reports `backend_reachable: false` and is labelled as fixture
  data everywhere, so a fixture-mode screenshot cannot be presented as live.
- A failed prediction clears the previous result card, and a failed RAG turn is
  not written into the RAG context used by suggestions and reports.

---

## 4. Defects found and fixed

All three were invisible to the fixture-only suite and were found by the new
backend-mode gate and browser journey.

| # | Defect | Impact | Fix |
|---|---|---|---|
| 1 | `source_context` carries raw uploaded-file bytes; posting it raised `TypeError: Object of type bytes is not JSON serializable` | **Upload → Dashboard was completely broken in backend mode.** The page died with a traceback on every upload. | The transport now replaces binary content with its byte length (`demo/services/backend_client.py`), covered by a regression test. |
| 2 | `dashboard_page.py` and `reports_page.py` indexed `response["data"]` directly | Any backend error produced a traceback instead of a message; the reports page crashed on `report_payload["sections"]`. | Both pages guard the response and render an explained gap. |
| 3 | Backend prediction responses omitted `model_version`, which `prediction_ui_contract.md` requires on every response | The UI's model-version footer would be empty against a real backend, breaking traceability from a prediction back to a model package. | The contract stub now serves the field; **the underlying gap is in the owner fixture and is raised against DV-TUONG-05** (see section 5). |

---

## 5. Contract issues to raise with other owners

These are UI-side observations that need the owning module to act. They are not
fixed by patching the UI.

1. **Prediction responses carry no `model_version`** (owner: Tường, relates to
   DV-TUONG-05). The Week 7 normalized fixture
   `demo/fixtures/week7/tuong_prediction_batch_response.json` has no
   `model_version` on any result, but the UI contract requires it on every
   response and the UI renders it. The backend contract stub currently fills the
   documented default so UI CI can run; the real service must emit it, together
   with the model checksum and threshold policy.

2. **Suggestion and report generation are backend routes but had no backend
   implementation.** The stub previously returned an empty list for
   `/suggestions/generate`, which meant backend-mode runs silently skipped past
   the Suggestions and Reports pages. The stub now serves the UI module's own
   reference implementation. The team needs to decide whether these routes stay
   UI-owned or move to the backend; the current contract document says the
   backend exposes them.

3. **RAG answers are retrieval-only.** The stub relabels a `retrieval_only`
   status as `success` while preserving `rag_generation_status` in metadata.
   Once Lập's DV-LAP-03 lands (non-empty, non-fallback answer required), the UI
   journey should assert on answer content, not only on citations.

---

## 6. Blockers

| Blocker | Owner | Effect |
|---|---|---|
| Canonical staging publishes Streamlit with no authentication | Duy | Staging must not be dispatched or shared until the proxy overlay and the `deploy-staging.yml` changes in `hung_week8_canonical_staging_gap.md` §2 land. |
| No staging URL has been issued | Duy (DV-DUY-08) | DV-HUNG-06 has nothing to run against. The pipeline exists; the deployment has not been performed. |
| No TLS termination for a staging hostname | Duy | Basic-auth credentials would cross the network in clear text, so the proxy must not be exposed yet. |
| Approved reviewer CIDR list undecided | Team | `STAGING_ALLOWED_CIDRS` has no real value to be set to. |
| Null `document_external_id` / `prediction_log_id` in generated fixtures | Tường | `scripts/week7_refresh_fixtures.py` reintroduces values the UI contract rejects, which fails the UI gate. |

No local screenshot should be presented as cloud staging evidence. Local runs
are deliberately labelled `environment: e2e` with release `e2e-local-run` so
they cannot be mistaken for one.

---

## 7. How to reproduce

```powershell
# Fixture-mode unit and contract suite
python -m pytest tests/

# DV-HUNG-01: mandatory backend-mode gate
python scripts/week8_backend_mode_gate.py

# DV-HUNG-02/03: browser journey (first time only: install the browser)
pip install -r requirements-e2e.txt
python -m playwright install chromium
python scripts/week8_run_browser_e2e.py

# DV-HUNG-06/07: the whole staging acceptance record, once a URL exists
python scripts/week8_staging_acceptance.py --ui-url <url> --release-sha <sha> `
  --allowlist-denied-verified
```

### Recorded results

```text
Fixture mode:   95 passed, 18 skipped
                (18 skips are backend-only tests, run by the gate below)

Backend mode:   113 passed, 0 failed, 0 skipped, 18 contract tests
                BACKEND-MODE GATE PASSED: no required backend test was skipped

Browser E2E:    4 passed, 10 screenshots
                BROWSER E2E GATE PASSED
                1/4 selected against a deployed URL; the other 3 are recorded
                in selection.excluded with their reason
```

The same gates on the canonical integration branch (`Intern6-Hung`, based on
`main` at `ca19091`): backend-mode 115 tests / 0 skipped, browser journey 4
passed / 10 screenshots, and `tests/ai_tests` unchanged at 18 passed.

Evidence artifacts:

```text
outputs/week8/hung_backend_mode_gate.json
outputs/week8/hung_backend_mode_junit.xml
outputs/week8/hung_browser_e2e.json
outputs/week8/hung_browser_e2e_junit.xml
screenshots/week8_browser_e2e/*.png
```

Both evidence files record the release SHA, the environment, the exact command,
and per-test outcomes, so a result can be traced to the build that produced it.

---

## 8. Files added or changed

**Added**

```text
demo/helpers/release_identity.py          release/environment/backend identity
demo/helpers/ui_status.py                 identity and failure rendering
demo/services/service_errors.py           failure classification and guidance
scripts/week8_backend_mode_gate.py        DV-HUNG-01 release gate
scripts/week8_run_browser_e2e.py          DV-HUNG-02/03/06 browser runner
tests/e2e/                                browser harness, journey, error suite
tests/test_release_identity.py            DV-HUNG-04 coverage
tests/test_service_error_contract.py      DV-HUNG-05 coverage
requirements-e2e.txt                      browser test dependency
pytest.ini                                marker configuration
deployment/staging/                       DV-HUNG-07 authenticated proxy
docs/W8/hung_week8_delivery_report.md     this report
docs/W8/hung_week8_staging_access_and_browser_validation.md
```

**Changed**

```text
demo/config.py                    release identity, split timeouts
demo/services/backend_client.py   classified errors, health, JSON-safe payloads
demo/services/mock_client.py      honest fixture-mode health
demo/services/service_client.py   health added to the service surface
demo/helpers/utils.py             real identity replaces hardcoded status
demo/views/home_page.py           real KPIs and health replace constants
demo/views/dashboard_page.py      per-dependency failure handling
demo/views/prediction_page.py     no stale result after a failure
demo/views/chatbot_page.py        failed retrieval not stored as context
demo/views/suggestions_page.py    guarded refresh
demo/views/reports_page.py        no draft without live evidence
backend_stub/main.py              health identity, contract completeness, faults
tests/test_backend_contract_smoke.py  fail-closed skip policy, health tests
tests/*                           contract tests pinned to the reference impl
.github/workflows/ci.yml          two new required jobs
```

---

## 9. Next actions

1. Open the owner PR from branch `Intern6-Hung` in the canonical repository. The
   branch is based on `main` at `ca19091` and touches no other owner's files;
   evidence is produced by the `ui-week8.yml` workflow and uploaded per commit
   SHA, so nothing has to be attached by hand.
2. Get the canonical changes in `hung_week8_canonical_staging_gap.md` §2 reviewed.
   Until they land, `deploy-staging.yml` must not be dispatched: it deploys an
   unauthenticated UI.
3. Raise the contract issues in section 5, plus the null
   `document_external_id` / `prediction_log_id` in the generated fixtures, with
   Tường and Lập.
4. Once a staging URL exists, one command closes both remaining tasks:
   `python scripts/week8_staging_acceptance.py --ui-url <url> --release-sha <sha>
   --allowlist-denied-verified`, run from inside `STAGING_ALLOWED_CIDRS` after
   confirming the 403 from outside it.

### Still unverified

The nginx proxy has not been started as a container. Its shell syntax, the
allowlist rendering, the fail-closed path and the merged `docker compose config`
against the real canonical stack are all verified; the container start-up path
itself is not, because no Docker daemon was available. Run
`docker compose --env-file .env.staging -f docker-compose.staging.yml
-f docker-compose.staging-proxy.yml up -d` on a host with Docker and confirm the
allowlist the proxy prints at start-up before relying on it.
