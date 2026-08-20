import os
import sys
from datetime import datetime, timezone

# Ensure project root is on sys.path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

def build_correction_payload(
    prediction_log_id: int,
    original_prediction: str,
    corrected_document_type: str,
    corrected_by: str,
    correction_reason: str = None,
    document_id: int = None,
    document_external_id: str = None,
) -> dict:
    """
    Build a database-ready payload for reviewer corrections.

    Parameters
    ----------
    prediction_log_id : int
        The log ID that is being corrected.
    original_prediction : str
        The original model prediction label.
    corrected_document_type : str
        The human corrected label.
    corrected_by : str
        The reviewer's username, email or ID.
    correction_reason : str, optional
        Explanation for why the prediction was changed/confirmed.
    document_id : int, optional
        Phat DB's document primary key.
    document_external_id : str, optional
        Duy's unique document external ID.

    Returns
    -------
    dict
        Database-ready dictionary format matching Phat's schema.
    """
    if not isinstance(prediction_log_id, int):
        raise TypeError("prediction_log_id must be an integer")

    if not str(original_prediction).strip():
        raise ValueError("original_prediction must be a non-empty string")

    if not str(corrected_document_type).strip():
        raise ValueError("corrected_document_type must be a non-empty string")

    if not str(corrected_by).strip():
        raise ValueError("corrected_by must be a non-empty string")

    return {
        "prediction_log_id": prediction_log_id,
        "document_id": document_id,
        "document_external_id": document_external_id,
        "original_prediction": str(original_prediction).strip(),
        "corrected_document_type": str(corrected_document_type).strip(),
        "corrected_by": str(corrected_by).strip(),
        "correction_reason": str(correction_reason).strip() if correction_reason else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
