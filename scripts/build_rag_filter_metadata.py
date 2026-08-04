import os
import sys
import json

# Resolve project root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

def build_rag_filter_metadata(prediction_result: dict, manual_reviewed: bool = False, trusted_model_version: bool = False) -> dict:
    """
    Build RAG filter metadata from a prediction result.
    """
    status = prediction_result.get("status")
    confidence = prediction_result.get("confidence", 0.0)

    use_for_rag_filtering = False
    filter_strength = "soft_metadata"
    reason = "Prediction not manually confirmed or below hard-filter threshold"

    if status == "accepted" and confidence >= 0.80:
        if manual_reviewed or trusted_model_version:
            use_for_rag_filtering = True
            filter_strength = "hard_filter"
            reason = "Prediction accepted and trusted"

    return {
        "document_external_id": prediction_result.get("document_external_id"),
        "document_db_id": prediction_result.get("document_db_id", prediction_result.get("document_id")),
        "predicted_document_type": prediction_result.get("predicted_document_type"),
        "confidence": confidence,
        "status": status,
        "use_for_rag_filtering": use_for_rag_filtering,
        "filter_strength": filter_strength,
        "reason": reason
    }

def main():
    input_path = os.path.join(_PROJECT_ROOT, "outputs", "week7_duy_prediction_results.json")
    output_path = os.path.join(_PROJECT_ROOT, "outputs", "rag_metadata", "document_type_filter_payload.json")

    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    rag_payloads = [build_rag_filter_metadata(r) for r in results]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rag_payloads, f, indent=2, default=str)

    print(f"Generated {len(rag_payloads)} RAG filter metadata payloads to {output_path}")

if __name__ == "__main__":
    main()
