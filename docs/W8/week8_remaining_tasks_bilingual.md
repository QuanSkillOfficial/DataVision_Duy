# DataVision Week 8 — Remaining Team Tasks / Các công việc còn lại của nhóm

**Document owner / Người phụ trách tài liệu:** Duy — CI/CD Lead  
**Release candidate / Bản phát hành ứng viên:** PR #5, `codex/week8-final-integration`  
**Current status / Trạng thái hiện tại:** Implementation and canonical CI passed; independent review, merge, and real cloud staging acceptance are pending. / Phần triển khai và canonical CI đã đạt; còn chờ review độc lập, merge và nghiệm thu trên cloud staging thật.

---

## 1. Definition of Done / Định nghĩa hoàn thành

### English

A task is complete only when all of the following are true:

1. The implementation is included in the canonical repository through a reviewed pull request.
2. All required CI jobs pass for the exact release commit.
3. Evidence identifies the exact Git SHA, image digest, environment, command, and result.
4. The task is executed against the real private staging environment when cloud evidence is required.
5. No P0 security, data-safety, contract, or deployment blocker remains.

Passing an owner-repository test or a local fixture test alone does not close a task.

### Tiếng Việt

Một task chỉ được xem là hoàn thành khi đáp ứng đầy đủ các điều kiện sau:

1. Phần triển khai đã được đưa vào canonical repository thông qua Pull Request có review.
2. Tất cả CI job bắt buộc đều xanh trên đúng release commit.
3. Evidence ghi rõ Git SHA, image digest, environment, câu lệnh và kết quả.
4. Task đã được chạy trên private cloud staging thật nếu yêu cầu bằng chứng cloud.
5. Không còn blocker P0 liên quan đến bảo mật, an toàn dữ liệu, contract hoặc deployment.

Việc test xanh trong owner repository hoặc chạy fixture cục bộ chưa đủ để đóng task.

---

## 2. Shared release gates / Các cổng release chung

### English

These gates block final closure for every owner:

1. Satyam or another independent authorized reviewer approves PR #5.
2. Auto-merge completes and produces the final commit on protected `main`.
3. All required CI jobs pass again for that final `main` SHA.
4. Backend, UI, and seed images are published with immutable SHA and digest references.
5. The `staging` Environment receives the real host, SSH, database, UI-authentication, CIDR, and HTTPS URL inputs.
6. The exact release is deployed to private cloud staging.
7. Cloud acceptance passes 15/15, browser E2E passes, and backup/restore/rollback evidence is retained.

### Tiếng Việt

Các cổng sau đang chặn việc đóng task của tất cả owner:

1. Satyam hoặc reviewer độc lập có thẩm quyền approve PR #5.
2. Auto-merge hoàn tất và tạo final commit trên protected branch `main`.
3. Toàn bộ CI job bắt buộc chạy xanh lại trên đúng final `main` SHA.
4. Backend, UI và seed images được publish bằng SHA và digest bất biến.
5. Environment `staging` được cung cấp host, SSH, database, UI authentication, CIDR và HTTPS URL thật.
6. Đúng release đó được deploy lên private cloud staging.
7. Cloud acceptance đạt 15/15, browser E2E đạt và lưu được evidence backup/restore/rollback.

---

## 3. Branch and Pull Request workflow / Quy trình Branch và Pull Request

### English

The code for all owner modules is already integrated into PR #5. Team members
must not recreate the same work, copy an entire owner repository into the
canonical repository, or push directly to `main`.

The required workflow is:

1. Complete the independent review and merge of PR #5 first.
2. After the merge, fetch the latest protected `main` from
   `QuanSkillOfficial/DataVision_Duy`.
3. Create a new branch from that exact `main` only when new code, tests,
   validation tooling, or versioned evidence must be committed.
4. Keep the branch limited to one owner and one closeout scope. Recommended
   branch names are:
   - Phat: `feat/phat-db-cloud-validation`
   - Lap: `feat/lap-rag-cloud-validation`
   - Tuong: `feat/tuong-prediction-cloud-validation`
   - Hung: `feat/hung-ui-cloud-e2e`
   - Duy: `feat/duy-staging-release`
5. Include only changes that are not already present in PR #5. Do not replay or
   merge an old conflicting branch into the new `main`.
6. Push the branch to the canonical repository and open a pull request targeting
   `main`.
7. Every pull request must identify:
   - task ID and owner;
   - source repository and source commit, when applicable;
   - changed files and scope boundaries;
   - test commands and CI results;
   - evidence JSON, logs, screenshots, or Actions artifacts;
   - dependencies and blockers;
   - release SHA and image digest for cloud evidence.
8. Obtain CODEOWNERS and independent reviewer approval before merge. Direct
   pushes to `main`, force pushes, and protection bypasses are not allowed.

Owner repositories remain useful for module development, but the accepted
release is defined only by the reviewed canonical `main`. An unmerged owner
branch is not the released implementation.

If cloud validation produces evidence without changing versioned source files,
an additional owner pull request is not mandatory. The owner may provide the
Actions artifact, query output, or screenshots to Duy, and Duy may consolidate
the approved evidence in the final release-acceptance pull request. Secrets,
private keys, passwords, tokens, and unrestricted infrastructure details must
never be committed as evidence.

### Tiếng Việt

Code của tất cả owner module đã được tích hợp trong PR #5. Các thành viên không
được làm lại cùng phần việc, copy toàn bộ owner repository vào canonical
repository hoặc push trực tiếp vào `main`.

Quy trình bắt buộc như sau:

1. Hoàn tất review độc lập và merge PR #5 trước.
2. Sau khi merge, lấy protected `main` mới nhất từ
   `QuanSkillOfficial/DataVision_Duy`.
3. Chỉ tạo branch mới từ đúng `main` đó khi cần commit code, test, validation
   tooling hoặc versioned evidence mới.
4. Mỗi branch chỉ giới hạn cho một owner và một phạm vi closeout. Tên branch đề
   xuất:
   - Phát: `feat/phat-db-cloud-validation`
   - Lập: `feat/lap-rag-cloud-validation`
   - Tường: `feat/tuong-prediction-cloud-validation`
   - Hưng: `feat/hung-ui-cloud-e2e`
   - Duy: `feat/duy-staging-release`
5. Chỉ đưa vào branch những thay đổi chưa có trong PR #5. Không replay hoặc
   merge branch cũ đang conflict vào `main` mới.
6. Push branch lên canonical repository và mở Pull Request vào `main`.
7. Mỗi Pull Request phải ghi rõ:
   - task ID và owner;
   - source repository và source commit nếu có;
   - các file thay đổi và giới hạn phạm vi;
   - lệnh test và kết quả CI;
   - evidence JSON, logs, screenshots hoặc Actions artifacts;
   - dependencies và blockers;
   - release SHA và image digest đối với cloud evidence.
8. Phải có CODEOWNERS và reviewer độc lập approve trước khi merge. Không được
   push trực tiếp vào `main`, force push hoặc vượt protection rules.

Owner repository vẫn được dùng để phát triển module, nhưng release được chấp
nhận chỉ được xác định bởi canonical `main` đã review. Branch trong owner repo
chưa merge không phải là bản release.

Nếu cloud validation chỉ tạo evidence và không thay đổi source file cần quản lý
phiên bản, owner không bắt buộc mở thêm Pull Request riêng. Owner có thể gửi
Actions artifact, query output hoặc screenshots cho Duy; Duy sẽ tổng hợp
evidence đã được duyệt trong final release-acceptance Pull Request. Tuyệt đối
không commit secrets, private keys, passwords, tokens hoặc thông tin hạ tầng
không được giới hạn vào evidence.

### Current repository decision / Quyết định cho repository hiện tại

- PR #5 remains the only canonical Week 8 release candidate and must be reviewed
  and merged before closeout branches are created. / PR #5 vẫn là release
  candidate Week 8 duy nhất và phải được review, merge trước khi tạo các branch
  closeout.
- Phat must not reuse the old conflicting database branch. / Phát không được tái
  sử dụng database branch cũ đang conflict.
- Lap and Tuong must not submit duplicate pull requests for code already included
  in PR #5. / Lập và Tường không mở Pull Request trùng lặp cho code đã nằm trong
  PR #5.
- Hung must not merge the complete owner `week8-hung-ui` branch directly into
  canonical `main`; only post-PR #5 fixes or evidence should be submitted from a
  clean branch. / Hưng không merge trực tiếp toàn bộ owner branch
  `week8-hung-ui` vào canonical `main`; chỉ gửi các sửa đổi hoặc evidence phát
  sinh sau PR #5 từ một branch sạch.

---

## 4. Duy — CI/CD Lead and Data Ingestion / Trưởng nhóm CI/CD và Data Ingestion

### English

**Completed:** ingestion CI, repository governance, CODEOWNERS, module provenance, fail-closed release verification, security/SBOM checks, immutable image publishing, protected deployment workflow, preflight diagnostics, backup-before-deploy integration, and rollback automation.

**Remaining P0 tasks:**

1. Obtain independent approval for PR #5 without bypassing branch protection.
2. Verify that the auto-merged `main` SHA has all required checks in the successful state.
3. Verify that published image manifests contain the same `main` SHA and record backend, UI, and seed digests.
4. Configure or validate the real staging inputs without exposing secret values:
   - `STAGING_HOST`
   - `STAGING_USER`
   - `STAGING_SSH_KEY`
   - `STAGING_KNOWN_HOSTS`
   - `POSTGRES_PASSWORD`
   - `STAGING_UI_PASSWORD`
   - `STAGING_ALLOWED_CIDRS`
   - public HTTPS UI URL
5. Dispatch the deployment using the final `main` SHA, not a pull-request head SHA.
6. Confirm remote preflight, exact-digest deployment, 15/15 acceptance, browser E2E, backup verification, access controls, and rollback results.
7. Publish the final acceptance report and release handoff with links to PR, CI, images, deployment, and evidence artifacts.

**Acceptance evidence:** final `main` SHA; successful required checks; image manifest/digests; deployment run URL; cloud acceptance JSON; browser JSON/screenshots; backup/restore evidence; rollback evidence; HTTPS staging URL.

### Tiếng Việt

**Đã hoàn thành:** ingestion CI, repository governance, CODEOWNERS, module provenance, fail-closed release verification, security/SBOM checks, publish immutable image, protected deployment workflow, preflight diagnostics, tích hợp backup trước deployment và rollback automation.

**Task P0 còn lại:**

1. Nhận approval độc lập cho PR #5 mà không vượt branch protection.
2. Xác nhận SHA được auto-merge lên `main` có toàn bộ required checks ở trạng thái thành công.
3. Xác nhận image manifest chứa đúng `main` SHA và lưu digest của backend, UI và seed image.
4. Cấu hình hoặc kiểm tra các đầu vào staging thật mà không làm lộ secret:
   - `STAGING_HOST`
   - `STAGING_USER`
   - `STAGING_SSH_KEY`
   - `STAGING_KNOWN_HOSTS`
   - `POSTGRES_PASSWORD`
   - `STAGING_UI_PASSWORD`
   - `STAGING_ALLOWED_CIDRS`
   - public HTTPS UI URL
5. Chạy deployment bằng final `main` SHA, không dùng PR head SHA.
6. Xác nhận remote preflight, deploy đúng digest, acceptance 15/15, browser E2E, backup verification, access controls và rollback.
7. Phát hành acceptance report và release handoff cuối cùng kèm link PR, CI, images, deployment và evidence artifacts.

**Evidence nghiệm thu:** final `main` SHA; required checks thành công; image manifest/digests; deployment run URL; cloud acceptance JSON; browser JSON/screenshots; backup/restore evidence; rollback evidence; HTTPS staging URL.

---

## 5. Phat — PostgreSQL and pgvector Safety / An toàn PostgreSQL và pgvector

### English

**Completed:** versioned migrations, migration/reference/demo-data separation, idempotent seeds, secret scanning, backup and restore tooling, database lifecycle tests, reviewer-correction migration, and canonical database CI.

**Remaining P0 tasks:**

1. Review the final canonical database tree and confirm that it matches the intended owner implementation.
2. Run migrations from zero on the real staging PostgreSQL/pgvector volume.
3. Run reference and demo seeds twice and prove that the second execution creates no duplicates.
4. Verify Duy documents/pages, Lap chunks/RAG logs, and Tuong prediction/review records using real database queries.
5. Create an automated backup immediately before deployment and verify it with `pg_restore --list`.
6. Restore the backup into an isolated database or volume and validate required tables, views, row counts, pgvector extension, and reviewer corrections.
7. Attach the evidence to the final release SHA and image digests.

**Acceptance evidence:** migration log; idempotency comparison; validation query output; backup metadata/checksum; restore log; restored row counts; pgvector check; final release identity.

**Repository hygiene:** merge or archive the owner feature branch after the canonical release is accepted; do not present an unmerged owner branch as the released version.

### Tiếng Việt

**Đã hoàn thành:** versioned migrations, tách migration/reference/demo data, seed idempotent, secret scanning, công cụ backup/restore, database lifecycle tests, migration cho reviewer correction và canonical database CI.

**Task P0 còn lại:**

1. Review cây database cuối trong canonical repo và xác nhận đúng với triển khai của owner.
2. Chạy migration từ volume trống trên PostgreSQL/pgvector staging thật.
3. Chạy reference và demo seed hai lần, chứng minh lần thứ hai không tạo duplicate.
4. Kiểm tra document/pages của Duy, chunks/RAG logs của Lập và prediction/review records của Tường bằng query database thật.
5. Tạo backup tự động ngay trước deployment và kiểm tra bằng `pg_restore --list`.
6. Restore backup vào database hoặc volume tách biệt; kiểm tra tables, views, row counts, pgvector extension và reviewer corrections.
7. Gắn evidence với final release SHA và image digests.

**Evidence nghiệm thu:** migration log; idempotency comparison; validation query output; backup metadata/checksum; restore log; row counts sau restore; pgvector check; final release identity.

**Vệ sinh repository:** merge hoặc archive owner feature branch sau khi canonical release được chấp nhận; không xem branch owner chưa merge là bản release.

---

## 6. Lap — RAG and pgvector Retrieval / RAG và truy xuất pgvector

### English

**Completed:** dependency-light CI mode, deterministic non-empty RAG response, citation-to-chunk validation, 384-dimensional vector contract, duplicate-safe indexing, stale-chunk cleanup, and canonical RAG CI.

**Remaining P0 tasks:**

1. Review the final canonical RAG tree and confirm owner intent and configuration provenance.
2. Index Duy's real staging `document_pages` into Phat's cloud pgvector database.
3. Repeat indexing and prove that chunk counts and stable identifiers do not duplicate.
4. Execute agreed RAG questions on cloud staging and prove each returned citation resolves to the retrieved document, page, and chunk.
5. Confirm that every successful response has non-empty evidence and that no empty or fallback-only response is reported as successful.
6. Persist and query RAG logs from PostgreSQL.
7. Store response JSON, retrieved chunks, similarity scores, citations, row counts, model/configuration identity, and release SHA.

**Acceptance evidence:** before/after/repeated chunk counts; cloud RAG response JSON; citation validation result; retrieved chunks and scores; RAG log query; embedding/config identity; final release SHA.

**Week 9/P1 follow-up:** replace the deterministic CI embedder with an approved semantic model and run a labelled retrieval-quality benchmark. This does not block the Week 8 integration demonstration if the limitation is stated clearly.

### Tiếng Việt

**Đã hoàn thành:** CI mode nhẹ dependency, RAG response xác định và không rỗng, kiểm tra citation với chunk, contract vector 384 chiều, indexing không duplicate, xóa stale chunks và canonical RAG CI.

**Task P0 còn lại:**

1. Review cây RAG cuối trong canonical repo và xác nhận đúng ý định/configuration provenance của owner.
2. Index `document_pages` thật của Duy vào cloud pgvector database của Phát.
3. Chạy indexing lặp lại và chứng minh chunk count cùng stable identifier không bị duplicate.
4. Chạy các câu hỏi RAG đã thống nhất trên cloud staging và chứng minh mỗi citation trỏ đúng document, page và chunk đã retrieve.
5. Xác nhận mọi response thành công đều có evidence không rỗng; không báo thành công cho response rỗng hoặc chỉ fallback.
6. Persist và query RAG logs trong PostgreSQL.
7. Lưu response JSON, retrieved chunks, similarity scores, citations, row counts, model/configuration identity và release SHA.

**Evidence nghiệm thu:** chunk counts trước/sau/lần chạy lặp; cloud RAG response JSON; citation validation result; retrieved chunks và scores; RAG log query; embedding/config identity; final release SHA.

**Theo dõi Week 9/P1:** thay deterministic CI embedder bằng semantic model được duyệt và chạy benchmark retrieval-quality có nhãn. Phần này không chặn demo tích hợp Week 8 nếu giới hạn được ghi rõ.

---

## 7. Tuong — Prediction and Review Workflow / Dự đoán và quy trình review

### English

**Completed:** canonical 20-payload batch, 15-item review fixture, response-contract fixes, model metadata and compatibility checks, OOD handling, failed-prediction acceptance gate, reviewer-correction code, and canonical prediction CI.

**Remaining P0 tasks:**

1. Review the final canonical prediction tree and confirm that model artifact, dependency versions, thresholds, labels, and response contracts are correct.
2. Run all 20 Duy payloads on the final release and retain the full prediction and prediction-log payloads.
3. Insert prediction logs into staging PostgreSQL and confirm that `failed` predictions cannot pass acceptance or enter a misleading successful UI state.
4. Submit a reviewer correction through the service/database path, read it back from PostgreSQL, and show it in the review queue.
5. Confirm that source, ingestion run, document, prediction-log, and review identifiers are not confused.
6. Expose model version, checksum, threshold policy, status, review reason, and OOD metadata in evidence.
7. Keep automatic acceptance disabled because the labelled Duy evaluation accuracy is currently 6.67%; use the human-review path until quality improves.

**Acceptance evidence:** 20-result batch JSON; prediction-log payloads; database insert/query output; failed-status gate result; reviewer-correction round trip; review-queue result; model identity; labelled evaluation; final release SHA.

**Week 9/P1 follow-up:** correct/expand labels, investigate feature mismatch, retrain or recalibrate the classifier, define an approved quality threshold, and rerun evaluation. The current result is suitable for a review-workflow demonstration, not production automatic classification.

### Tiếng Việt

**Đã hoàn thành:** canonical batch 20 payload, fixture review queue 15 items, sửa response contract, kiểm tra metadata/model compatibility, OOD handling, failed-prediction acceptance gate, code reviewer correction và canonical prediction CI.

**Task P0 còn lại:**

1. Review cây prediction cuối trong canonical repo và xác nhận model artifact, dependency versions, thresholds, labels và response contracts là chính xác.
2. Chạy đủ 20 payload của Duy trên final release và lưu toàn bộ prediction cùng prediction-log payload.
3. Insert prediction logs vào staging PostgreSQL; xác nhận prediction `failed` không thể vượt acceptance hoặc tạo trạng thái UI thành công sai lệch.
4. Gửi reviewer correction qua service/database path, đọc lại từ PostgreSQL và hiển thị trong review queue.
5. Xác nhận không nhầm source, ingestion run, document, prediction-log và review identifiers.
6. Đưa model version, checksum, threshold policy, status, review reason và OOD metadata vào evidence.
7. Giữ automatic acceptance ở trạng thái tắt vì accuracy trên labelled Duy evaluation hiện chỉ 6,67%; tiếp tục human review cho đến khi chất lượng được cải thiện.

**Evidence nghiệm thu:** batch JSON 20 kết quả; prediction-log payloads; database insert/query output; failed-status gate result; reviewer-correction round trip; review-queue result; model identity; labelled evaluation; final release SHA.

**Theo dõi Week 9/P1:** sửa/mở rộng labels, điều tra feature mismatch, retrain hoặc recalibrate classifier, thống nhất quality threshold và đánh giá lại. Kết quả hiện tại phù hợp để demo review workflow, chưa phù hợp phân loại tự động production.

---

## 8. Hung — Streamlit UI and Browser E2E / Streamlit UI và Browser E2E

### English

**Completed:** mandatory backend-mode gate, full Playwright user journey, release/backend identity, actionable service errors, stale-fixture protection, citation/report/suggestion checks, authenticated proxy implementation, IP-allowlist renderer, and canonical UI CI.

**Remaining P0 tasks:**

1. Review the final canonical UI tree and confirm that it contains all relevant owner fixes.
2. Run the browser journey against the real HTTPS private staging URL, not the local contract stub.
3. Verify the complete path: upload, ingestion status, dashboard, prediction/review status, RAG answer and citations, suggestions, report, and evidence table.
4. Verify negative paths: backend unavailable, timeout, invalid response, failed prediction, and no stale fixture success.
5. Validate staging access controls from allowed and disallowed networks:
   - unauthenticated request is rejected;
   - invalid credentials are rejected;
   - valid credentials from an allowed CIDR succeed;
   - a request outside the allowlist is rejected.
6. Confirm that the UI and backend display the exact final release SHA/image identity.
7. Upload per-run browser JSON, JUnit output, and fresh screenshots; stale screenshots must not satisfy the gate.

**Acceptance evidence:** cloud browser run URL; browser result JSON/JUnit; screenshots for the full journey and failure states; authentication/allowlist results; UI/backend release identity; final release SHA.

**Repository hygiene:** merge or archive the owner Week 8 branch after canonical acceptance and document how its final commits map to the canonical tree.

### Tiếng Việt

**Đã hoàn thành:** backend-mode gate bắt buộc, toàn bộ Playwright user journey, release/backend identity, service errors có hướng xử lý, ngăn stale fixture, kiểm tra citation/report/suggestion, authenticated proxy, IP-allowlist renderer và canonical UI CI.

**Task P0 còn lại:**

1. Review cây UI cuối trong canonical repo và xác nhận chứa đầy đủ các owner fixes cần thiết.
2. Chạy browser journey trên private staging HTTPS URL thật, không chạy bằng local contract stub.
3. Kiểm tra toàn bộ luồng: upload, ingestion status, dashboard, prediction/review status, RAG answer và citations, suggestions, report và evidence table.
4. Kiểm tra negative paths: backend unavailable, timeout, invalid response, failed prediction và không hiển thị stale fixture success.
5. Kiểm tra access controls từ mạng được phép và không được phép:
   - request không authentication bị từ chối;
   - credentials sai bị từ chối;
   - credentials đúng từ CIDR được phép thành công;
   - request ngoài allowlist bị từ chối.
6. Xác nhận UI và backend hiển thị đúng final release SHA/image identity.
7. Upload browser JSON, JUnit output và screenshots mới theo từng run; screenshot cũ không được dùng để vượt gate.

**Evidence nghiệm thu:** cloud browser run URL; browser result JSON/JUnit; screenshots toàn bộ journey và failure states; kết quả authentication/allowlist; UI/backend release identity; final release SHA.

**Vệ sinh repository:** merge hoặc archive owner Week 8 branch sau khi canonical release được chấp nhận và ghi lại mapping giữa final owner commits với canonical tree.

---

## 9. Phi / Team allocation note / Ghi chú phân công Phi

### English

Phi is not assigned new P0 implementation work in this closure plan because Satyam confirmed that Phi would no longer continue the CI/CD/UI workload. Hung and Duy now own the remaining UI integration and deployment gates. Any reassignment must be explicit and must include owner, reviewer, due date, and acceptance evidence.

### Tiếng Việt

Phi không được giao thêm phần triển khai P0 trong kế hoạch đóng task này vì Satyam đã xác nhận Phi không tiếp tục khối lượng CI/CD/UI. Hưng và Duy hiện chịu trách nhiệm các cổng UI integration và deployment còn lại. Mọi thay đổi phân công phải được xác nhận rõ owner, reviewer, deadline và acceptance evidence.

---

## 10. Required execution order / Thứ tự thực hiện bắt buộc

### English

1. Independent review and approval of PR #5.
2. Auto-merge to protected `main` and final CI verification.
3. Publish and record immutable image digests.
4. Configure approved staging secrets, CIDRs, host, and HTTPS URL.
5. Duy runs remote preflight; Phat validates from-zero database setup.
6. Duy deploys the exact release; Phat verifies backup and restore readiness.
7. Lap runs live indexing/retrieval; Tuong runs prediction logging and correction round trip.
8. Hung runs authenticated cloud browser E2E and access-control checks.
9. Duy runs acceptance 15/15 and the rollback drill.
10. Owners review their evidence; Duy publishes the final release handoff.

### Tiếng Việt

1. Review và approve độc lập PR #5.
2. Auto-merge vào protected `main` và kiểm tra final CI.
3. Publish và lưu immutable image digests.
4. Cấu hình staging secrets, CIDRs, host và HTTPS URL đã được phê duyệt.
5. Duy chạy remote preflight; Phát kiểm tra database setup từ volume trống.
6. Duy deploy đúng release; Phát kiểm tra backup và restore readiness.
7. Lập chạy live indexing/retrieval; Tường chạy prediction logging và correction round trip.
8. Hưng chạy authenticated cloud browser E2E và access-control checks.
9. Duy chạy acceptance 15/15 và rollback drill.
10. Các owner review evidence; Duy phát hành final release handoff.

---

## 11. Final closure statement / Tuyên bố đóng release

### English

Week 8 may be marked complete only when one clean canonical checkout passes CI, the same immutable images run on private cloud staging, the 15/15 acceptance and browser journey pass against that deployment, database recovery is demonstrated, and all evidence references the same release identity.

### Tiếng Việt

Week 8 chỉ được đánh dấu hoàn thành khi một canonical checkout sạch chạy CI thành công, cùng các immutable images đó chạy trên private cloud staging, acceptance 15/15 và browser journey đạt trên deployment đó, database recovery được chứng minh và toàn bộ evidence cùng tham chiếu một release identity.
