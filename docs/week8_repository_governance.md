# Week 8 Repository and Release Governance

## Canonical ownership and provenance

`integration/module_provenance.json` records five owner modules using an exact
source repository, imported source commit and commit URL, canonical path, and
canonical Git tree. `scripts/verify_module_provenance.py` runs as the first CI gate. A missing
module, untracked required file, nested repository, or unrecorded tree change
fails CI; owner jobs are never silently skipped.

The recorded source SHA describes the import lineage. Canonical integration
adaptations are represented by the canonical tree SHA and must not be described
as current owner-repository parity until the owner reviews the pull request.

| Module | Owner | Source SHA | Canonical path |
| --- | --- | --- | --- |
| Ingestion/integration | Duy | `ca19091095809047a143536186bd76d03f728449` | `data_engineering/` |
| PostgreSQL/pgvector | Phat | `b23cf0b1fd2312914acb4b8c870ba60122fa17e1` | `week7/database/`, `deployment/database/init/` |
| RAG/retrieval | Lap | `b1275fda7d3222d3c82972d9c224ddf858fc291f` | `ai/rag/`, `ai/ai_tests/` |
| Prediction | Tuong | `657c839b7471dcf5151c2314cfbe71b84a1a983f` | `ai/prediction/`, `tests/ai_tests/` |
| Streamlit UI | Hung | `2578af527696b9447db20a8194132a1eec394007` | `demo/` |

## Main-branch controls

`CODEOWNERS` assigns every module path to its owner and Duy as canonical
integrator. The provenance registry itself requests all five module owners.
Governance and deployment paths include an independent release reviewer so a
Duy-authored pull request cannot deadlock on self-approval. GitHub only enforces
Code Owners who retain repository write access, so collaborator access must be
audited whenever team membership changes. The intended `main` protection
contract is:

- pull requests only, with one approval and Code Owner review;
- required conversation resolution;
- required current CI checks, including module parity, owner suites, source
  security, and clean Compose acceptance;
- no force push or branch deletion;
- controlled staging credentials in the GitHub `staging` Environment.

Repository settings are remote state. Their live configuration must be
verified separately and retained as release evidence; this document alone is
not proof that GitHub protection is enabled.

## Immutable release identity

Both manual and automatic image publication reject a SHA unless it is reachable
from canonical `main` and has a successful `DataVision CI` run at that exact
commit. The release manifest binds that CI run to the release SHA and the
backend, UI, and seed registry digests. Deployment validates the manifest and
uses only `image@sha256` references; the server never builds application code.

Source scanning is mandatory in CI. Image scanning and CycloneDX SBOM creation
operate on the exact published digests. Fixable critical findings block the
release; high findings remain visible evidence and require a reviewed exception
or remediation before public promotion.

## Current release boundary

Local and CI staging acceptance are complete. Real private staging deployment
is not authorized by this change. It remains dependent on the reviewed owner
P0 gates: PostgreSQL backup/restore and migration safety, RAG answer/citation
acceptance, prediction failure rejection, and browser/backend-mode acceptance.
No public or production deployment is claimed.
