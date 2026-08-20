"""
train_model.py — Train document type classification models.

Usage:
    python ai/prediction/train_model.py

Steps:
    1. Load dataset
    2. Clean / preprocess data (via feature_builder)
    3. Encode labels
    4. Train/test split (80/20, stratified)
    5. Train Logistic Regression
    6. Train Random Forest
    7. Compare metrics (accuracy, macro P/R/F1)
    8. Select best model by Macro F1
    9. Save model package (.joblib)
   10. Save metrics JSON
"""

import json
import os
import sys

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------------------------
# Resolve project root so we can import feature_builder regardless of cwd
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.feature_builder import (
    CONFIDENCE_THRESHOLD,
    FEATURE_COLS,
    MODEL_NAME,
    MODEL_VERSION,
    TARGET_COL,
    build_preprocessor,
    clean_dataframe,
)

# ---------------------------------------------------------------------------
# Paths (relative to project root)
# ---------------------------------------------------------------------------
DATA_PATH = os.path.join(_PROJECT_ROOT, "datasets", "sample_document_classification.csv")
MODEL_DIR = os.path.join(_SCRIPT_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "best_document_type_classifier.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "model_metrics.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def evaluate_model(name: str, y_true, y_pred) -> dict:
    """Return a dict of metrics for one model."""
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    return {
        "model": name,
        "accuracy": round(float(accuracy), 6),
        "macro_precision": round(float(precision), 6),
        "macro_recall": round(float(recall), 6),
        "macro_f1": round(float(f1), 6),
    }


# ---------------------------------------------------------------------------
# Main training routine
# ---------------------------------------------------------------------------

def train(data_path: str = DATA_PATH) -> None:
    """Run the full training pipeline."""

    # 1. Load dataset -------------------------------------------------------
    print(f"[1/10] Loading dataset from {data_path}")
    df = pd.read_csv(data_path)
    print(f"       Dataset shape: {df.shape}")

    # 2. Clean / preprocess -------------------------------------------------
    print("[2/10] Cleaning and preprocessing data")
    df = clean_dataframe(df, fit_mode=True)

    # 3. Encode labels ------------------------------------------------------
    print("[3/10] Encoding labels")
    label_encoder = LabelEncoder()
    df["label"] = label_encoder.fit_transform(df[TARGET_COL])
    label_mapping = dict(
        zip(
            label_encoder.classes_.tolist(),
            label_encoder.transform(label_encoder.classes_).tolist(),
        )
    )
    print(f"       Label mapping: {label_mapping}")

    # 4. Train/test split ---------------------------------------------------
    print("[4/10] Splitting data (80/20, stratified)")
    X = df[FEATURE_COLS]
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"       Train size: {X_train.shape}  |  Test size: {X_test.shape}")

    # 5. Build preprocessor -------------------------------------------------
    preprocessor = build_preprocessor()

    # 6. Train Logistic Regression ------------------------------------------
    print("[5/10] Training Logistic Regression")
    lr_pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    lr_pipeline.fit(X_train, y_train)
    lr_pred = lr_pipeline.predict(X_test)

    # 7. Train Random Forest ------------------------------------------------
    print("[6/10] Training Random Forest")
    rf_pipeline = Pipeline([
        ("preprocess", build_preprocessor()),  # fresh preprocessor
        ("classifier", RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        )),
    ])
    rf_pipeline.fit(X_train, y_train)
    rf_pred = rf_pipeline.predict(X_test)

    # 8. Compare metrics ----------------------------------------------------
    print("[7/10] Comparing metrics")
    lr_metrics = evaluate_model("Logistic Regression", y_test, lr_pred)
    rf_metrics = evaluate_model("Random Forest", y_test, rf_pred)

    results = [lr_metrics, rf_metrics]
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))

    # 9. Select best model by Macro F1 --------------------------------------
    print("[8/10] Selecting best model by Macro F1")
    best_row = results_df.sort_values(by="macro_f1", ascending=False).iloc[0]
    best_model_name = best_row["model"]

    if best_model_name == "Logistic Regression":
        best_pipeline = lr_pipeline
        best_metrics = lr_metrics
    else:
        best_pipeline = rf_pipeline
        best_metrics = rf_metrics

    print(f"       Best model: {best_model_name}  (Macro F1 = {best_row['macro_f1']})")

    # 10a. Save model package ------------------------------------------------
    print("[9/10] Saving model package")
    os.makedirs(MODEL_DIR, exist_ok=True)

    import hashlib
    def get_file_hash(path: str) -> str:
        if not os.path.exists(path):
            return "fallback-data-hash"
        hasher = hashlib.md5()
        with open(path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    import sklearn
    training_data_version = get_file_hash(data_path)
    model_package = {
        "model": best_pipeline,
        "label_encoder": label_encoder,
        "feature_columns": FEATURE_COLS,
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "sklearn_version": sklearn.__version__,
        "training_data_version": training_data_version,
        "training_data_path": data_path,
    }
    joblib.dump(model_package, MODEL_PATH)
    print(f"       Saved model -> {MODEL_PATH}")

    # 10b. Save metrics JSON -------------------------------------------------
    print("[10/10] Saving metrics JSON")
    metrics_output = {
        "best_model": best_model_name,
        "best_metrics": best_metrics,
        "all_results": results,
        "label_mapping": label_mapping,
        "model_version": MODEL_VERSION,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "train_samples": int(X_train.shape[0]),
        "test_samples": int(X_test.shape[0]),
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, indent=2, ensure_ascii=False)
    print(f"       Saved metrics -> {METRICS_PATH}")

    print("\n[OK] Training complete!")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    train()
