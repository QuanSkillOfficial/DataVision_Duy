"""
evaluation.py — Evaluate the trained document type classifier.

Usage:
    python ai/prediction/evaluation.py

Outputs:
    - ai/prediction/models/evaluation_report.json
    - docs/model_report_week3.md
"""

import json
import os
import sys
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Resolve project root
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.feature_builder import (  # noqa: E402
    FEATURE_COLS,
    TARGET_COL,
    clean_dataframe,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_PATH = os.path.join(_PROJECT_ROOT, "datasets", "sample_document_classification.csv")
MODEL_PATH = os.path.join(_SCRIPT_DIR, "models", "best_document_type_classifier.joblib")
EVAL_REPORT_PATH = os.path.join(_SCRIPT_DIR, "models", "evaluation_report.json")
MODEL_REPORT_PATH = os.path.join(_PROJECT_ROOT, "docs", "model_report_week3.md")


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(
    data_path: str = DATA_PATH,
    model_path: str = MODEL_PATH,
) -> dict:
    """
    Evaluate the saved model on the test split and return a report dict.
    """

    # 1. Load dataset -------------------------------------------------------
    print(f"[1/5] Loading dataset from {data_path}")
    df = pd.read_csv(data_path)
    df = clean_dataframe(df, fit_mode=True)

    # 2. Load model package -------------------------------------------------
    print(f"[2/5] Loading model from {model_path}")
    pkg = joblib.load(model_path)
    model = pkg["model"]
    label_encoder = pkg["label_encoder"]
    model_version = pkg.get("model_version", "unknown")

    # 3. Reproduce the same train/test split --------------------------------
    print("[3/5] Reproducing train/test split")
    df["label"] = label_encoder.transform(df[TARGET_COL])
    X = df[FEATURE_COLS]
    y = df["label"]
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"       Test set size: {X_test.shape[0]} samples")

    # 4. Predict + metrics --------------------------------------------------
    print("[4/5] Computing metrics")
    y_pred = model.predict(X_test)
    classes = label_encoder.classes_.tolist()

    acc = float(accuracy_score(y_test, y_pred))
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="macro", zero_division=0
    )
    cls_report = classification_report(
        y_test, y_pred, target_names=classes, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_test, y_pred).tolist()

    report = {
        "model_version": model_version,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "test_samples": int(X_test.shape[0]),
        "accuracy": round(acc, 6),
        "macro_precision": round(float(prec), 6),
        "macro_recall": round(float(rec), 6),
        "macro_f1": round(float(f1), 6),
        "classification_report": cls_report,
        "confusion_matrix": cm,
        "class_labels": classes,
    }

    # 5. Print summary -------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"  Model version : {model_version}")
    print(f"  Accuracy      : {acc:.4f}")
    print(f"  Macro Precision: {prec:.4f}")
    print(f"  Macro Recall  : {rec:.4f}")
    print(f"  Macro F1      : {f1:.4f}")
    print(f"{'='*50}\n")
    print(classification_report(y_test, y_pred, target_names=classes, zero_division=0))

    return report


def save_evaluation_report(report: dict) -> None:
    """Save evaluation results as JSON and markdown."""

    # JSON report -----------------------------------------------------------
    os.makedirs(os.path.dirname(EVAL_REPORT_PATH), exist_ok=True)
    with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Saved evaluation report -> {EVAL_REPORT_PATH}")

    # Markdown report -------------------------------------------------------
    os.makedirs(os.path.dirname(MODEL_REPORT_PATH), exist_ok=True)
    md = _build_markdown_report(report)
    with open(MODEL_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Saved model report     -> {MODEL_REPORT_PATH}")


def _build_markdown_report(report: dict) -> str:
    """Generate a markdown model report from evaluation results."""

    classes = report["class_labels"]
    cm = report["confusion_matrix"]
    cls_report = report["classification_report"]

    lines: list[str] = []
    lines.append("# Model Report — Week 3\n")
    lines.append(f"**Model version**: `{report['model_version']}`  ")
    lines.append(f"**Evaluated at**: {report['evaluated_at']}  ")
    lines.append(f"**Test samples**: {report['test_samples']}\n")

    # Overall metrics table
    lines.append("## Overall Metrics\n")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Accuracy | {report['accuracy']:.4f} |")
    lines.append(f"| Macro Precision | {report['macro_precision']:.4f} |")
    lines.append(f"| Macro Recall | {report['macro_recall']:.4f} |")
    lines.append(f"| Macro F1 | {report['macro_f1']:.4f} |")
    lines.append("")

    # Per-class metrics
    lines.append("## Per-Class Metrics\n")
    lines.append("| Class | Precision | Recall | F1-Score | Support |")
    lines.append("|---|---|---|---|---|")
    for cls in classes:
        if cls in cls_report:
            c = cls_report[cls]
            lines.append(
                f"| {cls} | {c['precision']:.4f} | {c['recall']:.4f} "
                f"| {c['f1-score']:.4f} | {int(c['support'])} |"
            )
    lines.append("")

    # Confusion matrix
    lines.append("## Confusion Matrix\n")
    header = "| Actual \\ Predicted | " + " | ".join(classes) + " |"
    sep = "|---|" + "---|" * len(classes)
    lines.append(header)
    lines.append(sep)
    for i, cls in enumerate(classes):
        row_vals = " | ".join(str(v) for v in cm[i])
        lines.append(f"| **{cls}** | {row_vals} |")
    lines.append("")

    # Recommendations
    lines.append("## Recommendations\n")
    lines.append("1. The current model is trained on a **synthetic dataset** (500 samples). ")
    lines.append("   Results are promising but should not be treated as final real-world performance.")
    lines.append("2. Next steps:")
    lines.append("   - Evaluate on real uploaded documents with noisy OCR output.")
    lines.append("   - Add more training samples for underperforming classes.")
    lines.append("   - Monitor prediction confidence and manual correction rate in production.")
    lines.append("   - Consider adding human-in-the-loop review for low-confidence predictions.")
    lines.append("")

    return "\n".join(lines)


def generate_real_data_report(
    payloads_path: str = None,
    output_report_path: str = None,
) -> None:
    """Generate real-data evaluation report from canonical 20 payloads."""
    import json
    from ai.prediction.inference import predict_document_type

    if payloads_path is None:
        payloads_path = os.path.join(_PROJECT_ROOT, "tests", "ai_tests", "canonical_20_payloads.json")
    if output_report_path is None:
        output_report_path = os.path.join(_PROJECT_ROOT, "docs", "week8_real_data_evaluation.md")

    if not os.path.exists(payloads_path):
        print(f"Payloads file not found: {payloads_path}")
        return

    with open(payloads_path, "r", encoding="utf-8") as f:
        payloads = json.load(f)

    # Ground truth mapping
    ground_truth = {
        "doc_contract_01": "contract",
        "doc_contract_02": "contract",
        "doc_financial_01": "financial_statement",
        "doc_financial_02": "financial_statement",
        "doc_invoice_01": "invoice",
        "doc_invoice_02": "invoice",
        "doc_policy_01": "policy_document",
        "doc_policy_02": "policy_document",
        "doc_report_01": "report",
        "doc_report_02": "report",
        "doc_paper_01": "research_paper",
        "doc_paper_02": "research_paper",
        "doc_resume_01": "resume",
        "doc_resume_02": "resume",
        "doc_edge_short_text": None,
        "doc_missing_db_id": "contract",
        "doc_missing_source_name": "report",
        "doc_unknown_types": "report",
        "doc_empty_extracted_text": None,
        "doc_tricky_invoice": "invoice"
    }

    y_true = []
    y_pred = []
    confidences = []
    statuses = []

    for payload in payloads:
        doc_id = payload.get("document_external_id")
        gt = ground_truth.get(doc_id)

        result = predict_document_type(payload)
        pred = result.get("predicted_document_type")
        confidence = result.get("confidence", 0.0)
        status = result.get("status")

        confidences.append(confidence)
        statuses.append(status)

        if gt is not None and pred is not None:
            y_true.append(gt)
            y_pred.append(pred)

    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred) if y_true else 0.0
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    ) if y_true else (0.0, 0.0, 0.0, None)

    review_count = sum(1 for s in statuses if s == "needs_review")
    total_count = len(payloads)
    review_rate = review_count / total_count if total_count else 0.0

    bins = [0.0, 0.3, 0.5, 0.8, 1.0]
    hist, _ = np.histogram(confidences, bins=bins)

    lines = []
    lines.append("# Week 8 Real Data Prediction Evaluation\n")
    lines.append(f"**Evaluated at**: {datetime.now(timezone.utc).isoformat()}  ")
    lines.append(f"**Total Payloads**: {total_count}  ")
    lines.append(f"**Evaluated Samples (excluding edge cases)**: {len(y_true)}\n")

    lines.append("## Overall Performance Metrics\n")
    lines.append("| Metric | Value | Description |")
    lines.append("|---|---|---|")
    lines.append(f"| Accuracy | {accuracy:.2%} | Percentage of correct classifications |")
    lines.append(f"| Macro Precision | {precision:.4f} | Macro-averaged precision |")
    lines.append(f"| Macro Recall | {recall:.4f} | Macro-averaged recall |")
    lines.append(f"| Macro F1 | {f1:.4f} | Macro-averaged F1 score |")
    lines.append(f"| Review Rate | {review_rate:.2%} | Percentage of items routed to human review |")
    lines.append("")

    lines.append("## Confidence Calibration Distribution\n")
    lines.append("| Confidence Range | Count | Percentage |")
    lines.append("|---|---|---|")
    lines.append(f"| [0.0 - 0.3) | {hist[0]} | {hist[0]/total_count:.2%} |")
    lines.append(f"| [0.3 - 0.5) | {hist[1]} | {hist[1]/total_count:.2%} |")
    lines.append(f"| [0.5 - 0.8) | {hist[2]} | {hist[2]/total_count:.2%} |")
    lines.append(f"| [0.8 - 1.0] | {hist[3]} | {hist[3]/total_count:.2%} |")
    lines.append("")

    lines.append("## Status Breakdown\n")
    status_counts = {}
    for s in statuses:
        status_counts[s] = status_counts.get(s, 0) + 1
    lines.append("| Status | Count | Percentage |")
    lines.append("|---|---|---|")
    for s, c in status_counts.items():
        lines.append(f"| `{s}` | {c} | {c/total_count:.2%} |")
    lines.append("")

    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated Week 8 Real Data Evaluation Report -> {output_report_path}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    report = evaluate()
    save_evaluation_report(report)
    generate_real_data_report()
    print("\n[OK] Evaluation complete!")
