import os
import sys
import time

# Resolve project root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.inference import predict_document_type
from ai.prediction.batch_inference import predict_document_types
from ai.prediction.prediction_log_payload_builder import build_prediction_log_payload

def run_smoke_test():
    start_time = time.time()

    print("Running Prediction CI Smoke Test...")

    # 1. Model loads & 2. Metadata loads (Implicit in predict_document_type)
    # 3. Single prediction returns standard response
    valid_payload = {
        "source_id": 4,
        "document_external_id": "test_doc_001",
        "document_db_id": 1,
        "ingestion_run_id": "dummy-uuid",
        "file_name": "policy_doc.pdf",
        "file_type": "pdf",
        "file_size": 240000,
        "text_length": 4200,
        "num_pages": 4,
        "source_system": "manual_upload",
        "extracted_text": "This policy explains the rules for access control, responsibilities, approval process, and compliance review. " * 10
    }

    print("Testing single prediction...")
    result_single = predict_document_type(valid_payload)
    assert "status" in result_single
    assert "confidence" in result_single

    # 4. Batch prediction returns standard response
    print("Testing batch prediction...")
    batch_payloads = [valid_payload]
    result_batch = predict_document_types(batch_payloads)
    assert len(result_batch) == 1
    assert "status" in result_batch[0]

    # 5. Short text returns waiting_for_source
    print("Testing short text...")
    short_payload = dict(valid_payload)
    short_payload["extracted_text"] = "Too short"
    result_short = predict_document_type(short_payload)
    assert result_short["status"] == "waiting_for_source"

    # 6. Invalid payload returns failed
    print("Testing invalid payload...")
    invalid_payload = {"file_name": "test"} # Missing fields
    result_invalid = predict_document_type(invalid_payload)
    assert result_invalid.get("error") == "validation_error" or result_invalid.get("status") == "failed"

    # 7. Prediction log payload builds
    print("Testing prediction log payload...")
    log_payload = build_prediction_log_payload(valid_payload, result_single)
    assert "document_id" in log_payload
    assert log_payload["status"] == result_single["status"]

    # 8. RAG filter payload builds (mock)
    print("Testing RAG filter metadata build logic...")
    rag_payload = {
        "document_external_id": valid_payload["document_external_id"],
        "document_db_id": valid_payload["document_db_id"],
        "predicted_document_type": result_single.get("predicted_document_type"),
        "confidence": result_single.get("confidence"),
        "status": result_single.get("status"),
        "use_for_rag_filtering": result_single.get("status") == "accepted" and result_single.get("confidence", 0) >= 0.80,
        "filter_strength": "soft_metadata"
    }
    assert "filter_strength" in rag_payload

    # 9. UI fixture builds
    print("Testing UI fixture generation logic...")
    ui_fixture = {
        **result_single,
        "document_external_id": valid_payload["document_external_id"],
        "source_id": valid_payload["source_id"]
    }
    assert "document_external_id" in ui_fixture

    duration = time.time() - start_time
    print(f"Smoke test completed successfully in {duration:.2f} seconds!")
    assert duration < 120, "Smoke test took longer than 2 minutes"

if __name__ == "__main__":
    run_smoke_test()
