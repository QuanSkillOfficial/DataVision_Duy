# Output: week8\database\db_validation\idempotency_check.json
# Commands:
python "d:\Quansolution\Week\week8\database\scripts\run_database_setup.py" --smoke

python week8/database/scripts/idempotency_check.py after_run1

python "d:\Quansolution\Week\week8\database\scripts\run_database_setup.py" --smoke --skip-reset

python week8/database/scripts/idempotency_check.py after_run2

python week8/database/scripts/compare_idempotency.py week8/database/outputs/db_validation/idempotency_after_run1.json week8/database/outputs/db_validation/idempotency_after_run2.json > week8/database/outputs/db_validation/idempotency_check.json
# Results:
PS D:\Quansolution\Week> cat week8/database/outputs/db_validation/idempotency_check.json
{
  "pass": true,
  "tables": {
    "sources": {
      "run1": 4,
      "run2": 4,
      "match": true
    },
    "documents": {
      "run1": 1,
      "run2": 1,
      "match": true
    },
    "document_pages": {
      "run1": 36,
      "run2": 36,
      "match": true
    },
    "document_chunks": {
      "run1": 293,
      "run2": 293,
      "match": true
    },
    "structured_records": {
      "run1": 230,
      "run2": 230,
      "match": true
    },
    "ingestion_logs": {
      "run1": 4,
      "run2": 4,
      "match": true
    },
    "prediction_logs": {
      "run1": 10,
      "run2": 10,
      "match": true
    }
  }
}