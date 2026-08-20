# Week 8 Real Data Prediction Evaluation

**Evaluated at**: 2026-08-08T03:59:49.778553+00:00  
**Total Payloads**: 20  
**Evaluated Samples (excluding edge cases)**: 18

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

- **Mandatory Human Review**: Under the conservative staging acceptance threshold (`STAGING_ACCEPTANCE_THRESHOLD = 0.80`), 100% of non-failed/waiting documents (15/20) are routed to the manual review queue (`needs_review`).
- **Safety Gate**: Direct automatic acceptance into downstream production without reviewer confirmation is disabled until further training iterations.
- **Lineage Protection**: Any payload missing mandatory platform lineage (`document_external_id`) is strictly rejected as `failed` rather than entering the review queue without a valid identifier.
