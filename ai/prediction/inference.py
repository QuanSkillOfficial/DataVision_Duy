"""
inference.py — Predict document type from an input payload.

Usage (as a module):
    from ai.prediction.inference import predict_document_type

    result = predict_document_type({
        "file_name": "policy_doc.pdf",
        "file_type": "pdf",
        "file_size": 240000,
        "text_length": 4200,
        "num_pages": 4,
        "source_system": "manual_upload",
        "extracted_text": "This policy explains..."
    })

Usage (standalone demo):
    python ai/prediction/inference.py
"""

import os
import sys

import joblib
import numpy as np

# ---------------------------------------------------------------------------
# Resolve project root
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.feature_builder import (
    STATUS_ACCEPTED,
    STATUS_NEEDS_REVIEW,
    STATUS_WAITING_FOR_SOURCE,
    STATUS_FAILED,
    payload_to_dataframe,
    validate_input,
)
from ai.prediction.config import (
    STAGING_ACCEPTANCE_THRESHOLD,
    REVIEW_THRESHOLD,
    MIN_EXTRACTED_TEXT_LENGTH,
)

# ---------------------------------------------------------------------------
# Default model path
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(_SCRIPT_DIR, "models", "best_document_type_classifier.joblib")

# ---------------------------------------------------------------------------
# Model cache (loaded once)
# ---------------------------------------------------------------------------
_model_cache: dict | None = None


def _load_model(model_path: str = MODEL_PATH) -> dict:
    """Load and cache the model package."""
    global _model_cache
    if _model_cache is None:
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found: {model_path}. "
                "Run train_model.py first."
            )
        _model_cache = joblib.load(model_path)
    return _model_cache


def reset_model_cache() -> None:
    """Clear the cached model (useful for testing)."""
    global _model_cache
    _model_cache = None


# ---------------------------------------------------------------------------
# Main prediction function
# ---------------------------------------------------------------------------

def predict_document_type(
    input_payload: dict,
    *,
    model_path: str = MODEL_PATH,
) -> dict:
    """
    Predict the document type for a single input payload.

    Parameters
    ----------
    input_payload : dict
        Must contain the fields defined in feature_builder.REQUIRED_FIELDS.
    model_path : str
        Path to the .joblib model package.

    Returns
    -------
    dict
        On success:
            {
                "predicted_document_type": str,
                "confidence": float,
                "model_version": str,
                "status": "accepted" | "needs_review" | "waiting_for_source",
                "top_predictions": [{"label": str, "score": float}, ...],
                "review_reason": str | None,
            }
        On validation error:
            {
                "error": "validation_error",
                "message": str,
            }
    """

    # 1. Validate required fields -------------------------------------------
    errors = validate_input(input_payload)
    if errors:
        return {
            "error": "validation_error",
            "message": "; ".join(errors),
        }

    # 2. Input quality gate — check extracted_text length -------------------
    extracted_text = str(input_payload.get("extracted_text", "")).strip()
    if len(extracted_text) < MIN_EXTRACTED_TEXT_LENGTH:
        return {
            "predicted_document_type": None,
            "confidence": 0.0,
            "model_version": "document_classifier_v1",
            "status": STATUS_WAITING_FOR_SOURCE,
            "review_reason": "Extracted text is missing or too short for reliable prediction",
            "top_predictions": [],
        }

    # 3. Load model package -------------------------------------------------
    pkg = _load_model(model_path)
    model = pkg["model"]
    label_encoder = pkg["label_encoder"]
    model_version = pkg.get("model_version", "unknown")

    # 4. Convert payload → DataFrame ---------------------------------------
    df = payload_to_dataframe(input_payload)

    # 5. Predict class ------------------------------------------------------
    pred_label_id = model.predict(df)[0]
    predicted_type = label_encoder.inverse_transform([pred_label_id])[0]

    # 6. Compute confidence (predict_proba) ---------------------------------
    proba = model.predict_proba(df)[0]
    confidence = float(np.max(proba))

    # 7. Top-3 predictions --------------------------------------------------
    classes = label_encoder.classes_
    top_indices = np.argsort(proba)[::-1][:3]
    top_predictions = [
        {"label": str(classes[i]), "score": round(float(proba[i]), 4)}
        for i in top_indices
    ]

    # 8. Status -------------------------------------------------------------
    review_reason = None
    if confidence >= STAGING_ACCEPTANCE_THRESHOLD:
        status = STATUS_ACCEPTED
    elif confidence >= REVIEW_THRESHOLD:
        status = STATUS_NEEDS_REVIEW
        review_reason = "Confidence below staging threshold"
    else:
        status = STATUS_NEEDS_REVIEW
        review_reason = "Confidence below staging threshold"

    result: dict = {
        "predicted_document_type": str(predicted_type),
        "confidence": round(confidence, 4),
        "model_version": model_version,
        "status": status,
        "top_predictions": top_predictions,
        "review_reason": review_reason,
    }

    return result


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    sample_payload = {
        "file_name": "policy_doc.pdf",
        "file_type": "pdf",
        "file_size": 240000,
        "text_length": 4200,
        "num_pages": 4,
        "source_system": "manual_upload",
        "extracted_text": (
            "This policy explains the rules for access control, "
            "responsibilities, approval process, and compliance review."
        ),
    }

    print("=== Inference Demo ===")
    print(f"Input payload:\n{json.dumps(sample_payload, indent=2)}\n")

    output = predict_document_type(sample_payload)
    print(f"Prediction output:\n{json.dumps(output, indent=2)}")
