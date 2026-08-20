# Week 8 Real Data Prediction Evaluation

**Evaluated at**: 2026-08-08T03:59:49.778553+00:00

**Total Payloads**: 20

**Evaluated Samples (excluding edge cases)**: 18

## Canonical Release Decision

The release-quality metric is the labelled operational evaluation in
`outputs/prediction_evaluation/duy_week7_labeled_evaluation.json`: **1 of 15
comparable predictions correct (6.67% accuracy)**. This is the metric used by
the Week 8 release gate. The model is therefore suitable only for a
human-review-assisted staging demonstration; automatic acceptance remains
disabled.

## Owner Heuristic Evaluation (Legacy Comparison)

The figures below come from an earlier 18-sample owner heuristic evaluation.
They are retained for traceability, but **44.44% is not the canonical release
accuracy** and must not be used as the production-quality claim.

## Overall Performance Metrics

| Metric | Value | Description |
|---|---|---|
| Accuracy | 44.44% | Percentage of correct classifications |
| Macro Precision | 0.5714 | Macro-averaged precision |
| Macro Recall | 0.4405 | Macro-averaged recall |
| Macro F1 | 0.4535 | Macro-averaged F1 score |
| Review Rate | 75.00% | Percentage of items routed to human review |

## Confidence Calibration Distribution

| Confidence Range | Count | Percentage |
|---|---|---|
| [0.0 - 0.3) | 2 | 10.00% |
| [0.3 - 0.5) | 13 | 65.00% |
| [0.5 - 0.8) | 2 | 10.00% |
| [0.8 - 1.0] | 3 | 15.00% |

## Status Breakdown

| Status | Count | Percentage |
|---|---|---|
| `needs_review` | 15 | 75.00% |
| `failed` | 3 | 15.00% |
| `waiting_for_source` | 2 | 10.00% |
| `accepted` | 0 | 0.00% |

## Model Governance & Staging Safety

- **Canonical Accuracy**: The labelled Duy operational evaluation is 6.67% (1/15), so predictions are advisory rather than authoritative.
- **Mandatory Human Review**: Under the conservative staging acceptance threshold (`STAGING_ACCEPTANCE_THRESHOLD = 0.80`), 100% of non-failed/waiting documents (15/20) are routed to the manual review queue (`needs_review`).
- **Safety Gate**: Direct automatic acceptance into downstream production without reviewer confirmation is disabled until further training iterations.
- **Lineage Protection**: Any payload missing mandatory platform lineage (`document_external_id`) is strictly rejected as `failed` rather than entering the review queue without a valid identifier.
