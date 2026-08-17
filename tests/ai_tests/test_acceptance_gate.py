import os
import sys
import pytest

# Ensure project root is on sys.path
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.acceptance_gate import check_prediction_acceptance

def test_all_accepted_batch_passes():
    """A batch with only 'accepted' predictions must pass the gate."""
    results = [
        {"status": "accepted"},
        {"status": "accepted"},
        {"status": "accepted"}
    ]
    report = check_prediction_acceptance(results)
    assert report["passed"] is True
    assert report["total"] == 3
    assert report["accepted"] == 3
    assert report["needs_review"] == 0
    assert report["failed"] == 0
    assert report["rejected_indices"] == []

def test_mixed_accepted_and_review_passes():
    """A batch with a mix of 'accepted' and 'needs_review' must pass the gate."""
    results = [
        {"status": "accepted"},
        {"status": "needs_review"},
        {"status": "accepted"}
    ]
    report = check_prediction_acceptance(results)
    assert report["passed"] is True
    assert report["total"] == 3
    assert report["accepted"] == 2
    assert report["needs_review"] == 1
    assert report["failed"] == 0
    assert report["rejected_indices"] == []

def test_failed_status_fails_gate():
    """A batch containing any 'failed' status must fail the gate."""
    results = [
        {"status": "accepted"},
        {"status": "failed"},
        {"status": "needs_review"}
    ]
    report = check_prediction_acceptance(results)
    assert report["passed"] is False
    assert report["total"] == 3
    assert report["accepted"] == 1
    assert report["needs_review"] == 1
    assert report["failed"] == 1
    assert report["rejected_indices"] == [1]

def test_waiting_for_source_fails_gate():
    """A batch containing 'waiting_for_source' must fail the gate."""
    results = [
        {"status": "accepted"},
        {"status": "waiting_for_source"}
    ]
    report = check_prediction_acceptance(results)
    assert report["passed"] is False
    assert report["total"] == 2
    assert report["accepted"] == 1
    assert report["failed"] == 1  # count as failed in non-accepted counts
    assert report["rejected_indices"] == [1]
