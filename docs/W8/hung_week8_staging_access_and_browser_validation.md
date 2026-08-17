# Week 8 — Staging Access Control and Browser Validation Runbook

**Owner:** Hưng (Streamlit UI, backend contracts, user journey)
**Tasks:** DV-HUNG-06 (browser validation on private staging), DV-HUNG-07 (authenticated access)
**Status:** Implementation delivered and testable locally. Execution against a real
private staging host is **blocked** until Duy provides the deployed staging URL and host access.

---

## 1. Why the UI is never published directly

Streamlit serves the application on port 8501 with no authentication and no
authorization of its own. Anyone who can reach that port can:

- read every uploaded document and its extracted text,
- run predictions and see the review queue,
- ask RAG questions over indexed content,
- download generated reports.

So the Week 8 rule for this module is: **port 8501 is never bound to a public
interface.** Access always goes through an authenticating proxy.

---

## 2. What is delivered

| Artifact | Purpose |
|---|---|
| `deployment/staging/docker-compose.staging-ui.yml` | Removes the UI host port, keeps it on an internal network, and puts an authenticating proxy in front of it. |
| `deployment/staging/nginx-staging-ui.conf` | IP allowlist plus HTTP basic auth, with the websocket and timeout settings Streamlit needs. |
| `deployment/staging/render-allowlist.sh` | Renders the allowlist from `STAGING_ALLOWED_CIDRS` at container start and refuses to start when it is unset. |
| `deployment/staging/generate_htpasswd.sh` | Generates reviewer credentials; the resulting `htpasswd` file is git-ignored. |
| `scripts/week8_run_browser_e2e.py` | Runs the browser journey against any URL, including the staging URL. |
| `scripts/week8_staging_acceptance.py` | One command for the whole DV-HUNG-06/07 record: access-control checks plus the journey, into one evidence file. |
| `deployment/cloud/docker-compose.staging-proxy.yml` | Applies these controls to the canonical cloud staging stack, which publishes the UI unauthenticated. |

Two independent controls are used so that a single misconfiguration does not
expose the UI: the network allowlist and the reviewer credentials.

---

## 3. Deploying the protected staging UI

Run on the staging host, from the release checkout:

```bash
# 1. Reviewer credentials (record the printed password in the secret manager)
bash deployment/staging/generate_htpasswd.sh reviewer

# 2. Approved reviewer networks (space-separated; this is the whole allowlist)
export STAGING_ALLOWED_CIDRS="203.0.113.0/24 198.51.100.7/32"

# 3. Release identity that the UI must display (DV-HUNG-04)
export QS_RELEASE_SHA="<exact release sha>"
export QS_IMAGE_DIGEST="<sha256:... of the deployed UI image>"
export QS_ENVIRONMENT="staging"

# 4. Start the stack with the protected UI overlay
docker compose \
  -f docker-compose.yml \
  -f deployment/staging/docker-compose.staging-ui.yml \
  --profile ui up -d
```

`nginx-staging-ui.conf` carries no allowlist of its own. `STAGING_ALLOWED_CIDRS`
is rendered into `/etc/nginx/allowlist.conf` when the proxy starts, and the proxy
exits if the variable is unset or empty, so no deployment can inherit a default
network range that the team never approved. The rendered list is printed in the
proxy start-up log; check it there before sharing the URL.

---

## 4. Access control verification (DV-HUNG-07 acceptance)

One step that cannot be automated has to happen first, because it must come from
somewhere the allowlist rejects. Run this from a machine **outside**
`STAGING_ALLOWED_CIDRS` and confirm the result:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://<staging-host>/
# Expected: 403
```

Everything else is one command, run from a machine **inside** the allowlist. It
performs the remaining three access-control checks, then the browser journey, and
writes a single evidence file bound to one release SHA:

```bash
export QS_E2E_HTTP_USER=reviewer
export QS_E2E_HTTP_PASSWORD=...        # never pass this on the command line

python scripts/week8_staging_acceptance.py \
  --ui-url https://<staging-host> \
  --release-sha <exact release sha> \
  --allowlist-denied-verified          # only after the 403 above was confirmed
```

| Check | Expected |
|---|---|
| `direct_ui_port_unreachable` | TCP connect to the raw Streamlit port fails |
| `proxy_requires_authentication` | 401 without credentials |
| `authorised_reviewer_allowed` | 200 with reviewer credentials |
| `allowlist_denies_outside_networks` | 403, attested via `--allowlist-denied-verified` |
| `browser_journey_against_deployed_ui` | the journey passes with every required screenshot |

Two properties matter for review. The allowlist check **fails closed**: without
the attestation flag the run fails rather than reporting an unverified control as
green. And the browser journey runs only once the access controls hold, because a
green journey against an unprotected UI would be evidence of the wrong thing.

Result: `outputs/week8/hung_staging_acceptance.json`, generated rather than
transcribed, naming the exact release SHA, the URL and the reviewer account.

---

## 5. Browser validation on staging (DV-HUNG-06 acceptance)

The same browser journey that runs in CI is pointed at the staging URL. No
separate staging-only test exists, so a pass means the same assertions held
against the deployed release.

`week8_staging_acceptance.py` above already runs this step; the command below is
the same journey on its own, for a re-run without repeating the access checks.

```bash
pip install -r requirements-e2e.txt
python -m playwright install chromium

export QS_E2E_HTTP_USER=reviewer
export QS_E2E_HTTP_PASSWORD=...

python scripts/week8_run_browser_e2e.py \
  --base-url https://<staging-host> \
  --release-sha <exact release sha>
```

Credentials go in the environment, not in the URL: Chromium does not attach
credentials embedded in a URL to Streamlit's websocket and XHR requests, so the
first page would load and every rerun after it would 401.

Against a deployed URL only the staging-capable tests run. The three that need a
UI they control - a dead backend, or the stub's fault-injection route - are
recorded in the evidence file under `selection.excluded` with the reason, rather
than skipped silently.

Outputs:

```text
screenshots/week8_browser_e2e/*.png      browser evidence for each journey step
outputs/week8/hung_browser_e2e.json      pass/fail tied to the release SHA
outputs/week8/hung_browser_e2e_junit.xml per-test results
```

The run fails if any journey step is missing its screenshot, so incomplete
evidence cannot be reported as a pass.

### What the staging run must show

- The UI header reports `environment: staging` and the exact deployed release SHA.
- The UI and backend report the **same** release SHA (`release_match` is not `mismatch`).
- Upload, dashboard, prediction, review status, RAG, citations, suggestions and
  reports all succeed against the deployed backend.
- No page renders a service-error block during the successful journey.

---

## 6. Current blockers

| Blocker | Owner | Impact |
|---|---|---|
| No private staging host or URL exists yet | Duy (DV-DUY-08) | DV-HUNG-06 cannot be executed; only the local stack has been validated. |
| No TLS certificate or terminating load balancer for the staging hostname | Duy | Basic auth credentials would otherwise cross the network in clear text. |
| Approved reviewer CIDR list not yet decided | Team | `STAGING_ALLOWED_CIDRS` cannot be set to a real value. |

Until these are resolved, the honest status for DV-HUNG-06 and DV-HUNG-07 is
**implemented and locally verified, not executed on a real private staging
host**. No screenshot from a local run should be presented as cloud staging
evidence: local runs are labelled `environment: e2e` and carry the release SHA
`e2e-local-run` precisely so they cannot be mistaken for one.
