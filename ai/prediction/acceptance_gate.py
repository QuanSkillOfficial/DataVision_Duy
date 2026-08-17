import os
import sys

# Resolve project root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.config import RELEASE_GATE_ALLOWED_STATUSES

def check_prediction_acceptance(results: list[dict]) -> dict:
    """
    Check if a batch of prediction results passes the release gate.
    
    A batch passes only if every prediction has a status of 'accepted' or 'needs_review'.
    Any status like 'failed' or 'waiting_for_source' will trigger a gate failure.
    
    Parameters
    ----------
    results : list[dict]
        List of prediction result dictionaries.
        
    Returns
    -------
    dict
        {
            "passed": bool,
            "total": int,
            "accepted": int,
            "needs_review": int,
            "failed": int,
            "rejected_indices": list[int]
        }
    """
    total = len(results)
    accepted = 0
    needs_review = 0
    failed = 0
    rejected_indices = []

    for i, result in enumerate(results):
        status = result.get("status")
        if status == "accepted":
            accepted += 1
        elif status == "needs_review":
            needs_review += 1
        else:
            failed += 1
            
        if status not in RELEASE_GATE_ALLOWED_STATUSES:
            rejected_indices.append(i)

    passed = len(rejected_indices) == 0

    return {
        "passed": passed,
        "total": total,
        "accepted": accepted,
        "needs_review": needs_review,
        "failed": failed,
        "rejected_indices": rejected_indices
    }
