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


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    report = evaluate()
    save_evaluation_report(report)
    print("\n[OK] Evaluation complete!")
