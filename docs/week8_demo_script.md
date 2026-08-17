# Week 8 Demo Script — Prediction Module Hardening & Staging Release

> **Presenter:** Tuong  
> **Module:** Prediction & Model Governance  
> **Estimated Duration:** ~10–15 minutes  
> **Objective:** Demonstrate the completion of all 7 assigned tasks (DV-TUONG-01 through DV-TUONG-07) to harden the prediction module for the staging release, ensuring reproducibility, safety gates, OOD detection, metadata traceability, and real-data evaluation.

---

## 1. Introduction (~1 minute)

**Speech:**
> "Hello everyone. Today I'm going to demonstrate the hardening of the Prediction module for our Week 8 Staging Release. We have transitioned from basic integration to production-level reliability by pinning our dependencies, validating artifact compatibility, enforcing release safety gates, introducing Out-of-Distribution detection, and generating a traceable real-data evaluation report."

---

## 2. Dependency Pinning & Model Compatibility Check (DV-TUONG-01 & DV-TUONG-03) (~2 minutes)

**Speech:**
> "First, we ensure complete environment reproducibility. In `requirements.txt`, we have pinned all core libraries (pandas, numpy, joblib, scikit-learn) to their exact versions. To prevent silent failures when model files are loaded, we now save the scikit-learn version inside the model artifact and validate it at runtime. If there is a version mismatch, we fail early with a clear exception."

**Show:**
1. Open [requirements.txt](file:///f:/Quanskill/requirements.txt) to show exact version pins:
   - `pandas==2.2.3`
   - `numpy==1.26.4`
   - `scikit-learn==1.7.2`
   - `joblib==1.5.0`
2. Open [inference.py](file:///f:/Quanskill/ai/prediction/inference.py) at the `_load_model` function to point out the `sklearn_version` check.
3. Run the model compatibility tests to demonstrate mismatch protection:
   ```bash
   python -m pytest tests/ai_tests/test_model_artifact_compatibility.py -v
   ```

---

## 3. Canonical 20-Payload Evidence (DV-TUONG-02) (~2 minutes)

**Speech:**
> "To guarantee our service correctly processes diverse document inputs under our staging thresholds, we established a canonical set of 20 payloads. This covers all 7 supported document types (contracts, financial statements, invoices, policies, reports, papers, resumes) along with tricky layouts and edge cases (such as missing IDs, unknown file types, and empty text). We've written a test to execute all 20 payloads and generate our synchronized output evidence."

**Show:**
1. Open [canonical_20_payloads.json](file:///f:/Quanskill/tests/ai_tests/canonical_20_payloads.json) to showcase the diverse payload inputs.
2. Execute the canonical test flow:
   ```bash
   python -m pytest tests/ai_tests/test_canonical_20_payload.py -v
   ```
3. Open [canonical_20_results.json](file:///f:/Quanskill/outputs/canonical_20_results.json) to show the generated prediction results and DB-ready log payloads aligned with the current Git Release SHA.

---

## 4. Release Gate Enforcement (DV-TUONG-04) (~2 minutes)

**Speech:**
> "A major safety concern was ensuring that failed predictions do not slip into our downstream staging services. We implemented an explicit acceptance gate module. A batch of predictions will only pass if every item resolves to either `accepted` or `needs_review`. Any item marked as `failed` or `waiting_for_source` immediately rejects the entire batch."

**Show:**
1. Open [config.py](file:///f:/Quanskill/ai/prediction/config.py) showing `RELEASE_GATE_ALLOWED_STATUSES = ["accepted", "needs_review"]`.
2. Open [acceptance_gate.py](file:///f:/Quanskill/ai/prediction/acceptance_gate.py) to highlight the `check_prediction_acceptance` function.
3. Run the gate checks test suite:
   ```bash
   python -m pytest tests/ai_tests/test_acceptance_gate.py -v
   ```

---

## 5. Model Metadata Exposure & Traceability (DV-TUONG-05) (~2 minutes)

**Speech:**
> "For governance and logging purposes, every single prediction response must be traceable back to the exact training data and policy. We modified our inference responses to return the `model_checksum` (MD5 of the .joblib file), `training_data_version` (hash of the training CSV), and the active `threshold_policy` (staging and review thresholds)."

**Show:**
1. Open [inference.py](file:///f:/Quanskill/ai/prediction/inference.py) showing the updated dictionary output inside `predict_document_type()`.
2. Run the metadata exposure test:
   ```bash
   python -m pytest tests/ai_tests/test_model_metadata_exposure.py -v
   ```

---

## 6. Out-of-Distribution (OOD) Detection & Feedback Corrections (DV-TUONG-06) (~2 minutes)

**Speech:**
> "To handle completely new or highly ambiguous document inputs, we added Out-of-Distribution (OOD) detection. If the model's confidence is below `OOD_THRESHOLD = 0.30`, we automatically tag it as `is_out_of_distribution: true` and route it to the manual review queue with a specific reason. In addition, we created a builder to prepare structured corrections payloads that Phat can persist in PostgreSQL."

**Show:**
1. Open [config.py](file:///f:/Quanskill/ai/prediction/config.py) showing `OOD_THRESHOLD = 0.30`.
2. Open [reviewer_corrections.py](file:///f:/Quanskill/ai/prediction/reviewer_corrections.py) and show `build_correction_payload()`.
3. Run the OOD and correction tests:
   ```bash
   python -m pytest tests/ai_tests/test_ood_detection.py -v
   ```

---

## 7. Real Data Evaluation Report (DV-TUONG-07) (~2 minutes)

**Speech:**
> "Finally, we generated a comprehensive evaluation report on our canonical real payloads. The report details the accuracy, macro F1, confidence calibration histogram, and manual review rate. Due to our conservative staging acceptance threshold (0.80), most real-world documents are correctly routed to the manual review queue (75% review rate), ensuring absolute safety for staging operations."

**Show:**
1. Execute the main evaluation runner:
   ```bash
   python ai/prediction/evaluation.py
   ```
2. Open and present the generated report: [week8_real_data_evaluation.md](file:///f:/Quanskill/docs/week8_real_data_evaluation.md)
   - Highlight the **44.44% Accuracy** and **0.4535 F1 Score** on real data.
   - Point out the **75% Review Rate** (15 out of 20 items routed to review).
   - Show the **Confidence Calibration Distribution** table.

---

## 8. CI Readiness Verification (Task 8) (~1 minute)

**Speech:**
> "To verify that our entire codebase is fully stable and ready to merge into GitHub Actions, I will execute the complete Pytest suite."

**Show:**
1. Run all unit tests:
   ```bash
   python -m pytest
   ```
2. Point out that **all 128 tests passed successfully with 0 failures** in under 3 seconds.

---

## Conclusion (~30 seconds)

**Speech:**
> "This concludes our Week 8 hardening presentation. The prediction module is now fully traceable, compatible, OOD-protected, and guarded by safety gates, ready for the MVP integration. Thank you!"
