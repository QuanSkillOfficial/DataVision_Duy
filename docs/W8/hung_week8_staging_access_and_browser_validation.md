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
| `scripts/week8_run_browser_e2e.py` | Runs the full browser journey against any URL, including the staging URL. |

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

Run all four checks and keep the output as evidence. The task is not complete
until every one produces the expected result.

```bash
# 4.1 The UI port must NOT be reachable from outside the host.
curl -sS --max-time 5 http://<staging-host>:8501/ ; echo "exit=$?"
# Expected: connection refused or timeout (non-zero exit).

# 4.2 The proxy must reject an unauthenticated request.
curl -sS -o /dev/null -w '%{http_code}\n' https://<staging-host>/
# Expected: 401

# 4.3 The proxy must reject a request from outside the allowlist.
#     Run from a machine that is not in STAGING_ALLOWED_CIDRS.
curl -sS -o /dev/null -w '%{http_code}\n' https://<staging-host>/
# Expected: 403

# 4.4 An approved reviewer with credentials must get through.
curl -sS -o /dev/null -w '%{http_code}\n' -u reviewer:<password> https://<staging-host>/
# Expected: 200
```

Record the results in `outputs/week8/hung_staging_access_check.md` together with
the date, the host, and the release SHA that was deployed.

---

## 5. Browser validation on staging (DV-HUNG-06 acceptance)

The same browser journey that runs in CI is pointed at the staging URL. No
separate staging-only test exists, so a pass means the same assertions held
against the deployed release.

```bash
pip install -r requirements-e2e.txt
python -m playwright install chromium

python scripts/week8_run_browser_e2e.py \
  --base-url https://reviewer:<password>@<staging-host> \
  --release-sha <exact release sha>
```

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
