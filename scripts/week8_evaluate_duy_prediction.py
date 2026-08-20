"""Evaluate Tuong's classifier against Duy's versioned Week 7 handoff set."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from ai.prediction.inference import predict_document_type


PAYLOAD_DIR = ROOT / "outputs/prediction_payloads/week7"
LABELS_PATH = ROOT / "ai/prediction/evaluation/duy_week7_labels.json"
JSON_OUTPUT = ROOT / "outputs/prediction_evaluation/duy_week7_labeled_evaluation.json"
REPORT_OUTPUT = ROOT / "docs/week8_duy_labeled_prediction_evaluation.md"


def evaluate() -> dict:
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    mapping = labels["labels_by_file"]
    payload_files = sorted(PAYLOAD_DIR.glob("*.json"))
    actual_names = {path.name for path in payload_files}
    if actual_names != set(mapping):
        raise ValueError(
            "Label manifest and Duy payload set differ: "
            f"missing_labels={sorted(actual_names - set(mapping))}, "
            f"missing_payloads={sorted(set(mapping) - actual_names)}"
        )

    rows: list[dict] = []
    y_true: list[str] = []
    y_pred: list[str] = []
    for path in payload_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = predict_document_type(payload)
        expected = mapping[path.name]
        predicted = result.get("predicted_document_type")
        if expected is not None and predicted is not None:
            y_true.append(expected)
            y_pred.append(predicted)
        rows.append(
            {
                "payload_file": path.name,
                "document_external_id": payload.get("document_external_id"),
                "expected_document_type": expected,
                "predicted_document_type": predicted,
                "confidence": result.get("confidence", 0.0),
                "status": result.get("status", "failed"),
                "is_out_of_distribution": result.get("is_out_of_distribution", False),
                "included_in_quality_metrics": expected is not None and predicted is not None,
            }
        )

    accuracy = accuracy_score(y_true, y_pred) if y_true else 0.0
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    ) if y_true else (0.0, 0.0, 0.0, None)
    first_result = predict_document_type(
        json.loads(payload_files[0].read_text(encoding="utf-8"))
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "payload_directory": "outputs/prediction_payloads/week7",
            "label_manifest": "ai/prediction/evaluation/duy_week7_labels.json",
            "label_basis": labels["label_basis"],
            "payload_source_sha": labels["payload_source_sha"],
            "prediction_source_sha": labels["prediction_source_sha"],
            "total_payloads": len(rows),
            "labeled_payloads": len(y_true),
            "excluded_validation_payloads": len(rows) - len(y_true),
            "scope_note": (
                "This operational handoff set is report-dominant; use the canonical "
                "multi-class set for broad model-quality comparison."
            ),
        },
        "model": {
            "model_version": first_result.get("model_version"),
            "model_checksum": first_result.get("model_checksum"),
            "training_data_version": first_result.get("training_data_version"),
            "threshold_policy": first_result.get("threshold_policy"),
        },
        "metrics": {
            "accuracy": round(float(accuracy), 6),
            "macro_precision": round(float(precision), 6),
            "macro_recall": round(float(recall), 6),
            "macro_f1": round(float(f1), 6),
            "status_counts": dict(Counter(row["status"] for row in rows)),
        },
        "results": rows,
    }


def markdown(evidence: dict) -> str:
    dataset = evidence["dataset"]
    metrics = evidence["metrics"]
    status_rows = "\n".join(
        f"| `{status}` | {count} |" for status, count in sorted(metrics["status_counts"].items())
    )
    return f"""# Week 8 Duy-labelled Prediction Evaluation

- Generated at: `{evidence['generated_at']}`
- Duy payload source SHA: `{dataset['payload_source_sha']}`
- Tuong prediction source SHA: `{dataset['prediction_source_sha']}`
- Payloads: {dataset['total_payloads']} total, {dataset['labeled_payloads']} labelled, {dataset['excluded_validation_payloads']} validation-only
- Label basis: {dataset['label_basis']}
- Scope: {dataset['scope_note']}

## Metrics

| Metric | Value |
|---|---:|
| Accuracy | {metrics['accuracy']:.2%} |
| Macro precision | {metrics['macro_precision']:.4f} |
| Macro recall | {metrics['macro_recall']:.4f} |
| Macro F1 | {metrics['macro_f1']:.4f} |

## Status counts

| Status | Count |
|---|---:|
{status_rows}

The machine-readable per-document results and model metadata are stored in
`outputs/prediction_evaluation/duy_week7_labeled_evaluation.json`.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate and evaluate without writing evidence")
    args = parser.parse_args()
    evidence = evaluate()
    if evidence["dataset"]["total_payloads"] != 20:
        raise ValueError("The Duy evaluation contract requires exactly 20 payloads")
    if evidence["dataset"]["labeled_payloads"] < 10:
        raise ValueError("The Duy evaluation requires a meaningful labelled subset")
    if not args.check:
        JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        JSON_OUTPUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        REPORT_OUTPUT.write_text(markdown(evidence), encoding="utf-8")
        print(f"Wrote {JSON_OUTPUT.relative_to(ROOT)} and {REPORT_OUTPUT.relative_to(ROOT)}")
    else:
        print(json.dumps({"status": "passed", "metrics": evidence["metrics"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
