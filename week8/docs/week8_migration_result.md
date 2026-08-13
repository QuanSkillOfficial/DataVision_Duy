## Output: week8\database\outputs\backups
## 1. Current Migration Version
The database setup has been successfully transitioned from a single initialization script to a versioned migration lifecycle. The current active migrations in the `week8/database/migrations/` directory are:
*   `0001_init_schema.sql`: Contains the baseline Week 7 schema (10 core tables), all indexes, enables the `pgvector` extension, and establishes the `schema_migrations` tracking table.
*   `0002_create_analytics_views.sql`: Contains the definitions for the 12 required analytical views.

## 2. Test Scenario 1: Fresh Install (Empty Database)
**Objective:** Verify that a completely empty database can be initialized from scratch and pass all validation checks.

**Command executed:**
PS D:\Quansolution\Week> python d:\Quansolution\Week\week8\database\migrations\run_database_setup.py
[23:52:10] ======================================================================
[23:52:10] Week 8 Database Setup - starting fresh setup from zero
[23:52:10] Target DB: datavision@localhost:5432/datavision_db
[23:52:10] ======================================================================
[23:52:10] --- Running: Step 0/9: Backup database ---
[23:52:10] Command: C:\Users\ACER\AppData\Local\Programs\Python\Python310\python.exe week8\database\scripts\backup_database.py
Backup OK: week8\database\outputs\backups\datavision_db_20260812_235210.dump
[23:52:11] Database backup completed
[23:52:11] --- Running: Step 1/9: Reset database ---
[23:52:11] Command: psql -h localhost -p 5432 -U datavision -d datavision_db -v ON_ERROR_STOP=1 -f week8\database\scripts\reset_database_v2.sql
DROP VIEW
DROP VIEW
DROP VIEW
DROP VIEW
DROP VIEW
DROP VIEW
DROP VIEW
DROP VIEW
DROP VIEW
DROP VIEW
DROP VIEW
DROP VIEW
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
[23:52:11] Database reset completed
[23:52:11] --- Running: Step 2-4/9: Apply versioned migrations ---
[23:52:11] Command: C:\Users\ACER\AppData\Local\Programs\Python\Python310\python.exe week8\database\migrations\run_migrations.py
--- Starting Database Migrations ---
Applying migration: 0001_init_schema.sql...
Success: 0001_init_schema.sql
Applying migration: 0002_create_analytics_views.sql...
Success: 0002_create_analytics_views.sql
--- Migrations Completed ---
[23:52:12] Migrations applied
[23:52:12] Schema created
[23:52:12] Views created
[23:52:12] --- Running: Step 5/9: Load Duy sample/real outputs ---
[23:52:12] Command: C:\Users\ACER\AppData\Local\Programs\Python\Python310\python.exe week8\scripts\load_data.py
🧹 Cleaning up existing data...
✅ Loaded: sources, pipeline_runs, ingestion_logs (from ingestion_runs.jsonl)
✅ Loaded: documents (from pdf_metadata.json)
✅ superstore_sales_csv: loaded 9994 rows into structured_records
✅ product_sales_region_excel: loaded 1500 rows into structured_records
✅ dummyjson_products_api: loaded 30 rows into structured_records
✅ document_pages: loaded 36 rows

🎉 Done. Changes have been committed to the database.
   - sources:            4 rows
   - pipeline_runs:      4 rows
   - ingestion_logs:     4 rows
   - documents:          1 rows
   - document_pages:     36 rows
   - structured_records: 11524 rows
   - Đã lưu file kết quả tại: week8\database\outputs\db_validation\duy_data_load_counts.json
[23:52:14] Duy data loaded
[23:52:14] --- Running: Step 6/9: Load Tuong prediction logs ---
[23:52:14] Command: C:\Users\ACER\AppData\Local\Programs\Python\Python310\python.exe week8\scripts\insert_prediction_logs_to_postgres.py --input week8\scripts\week6_duy_prediction_results.json
Loading payloads from: week8\scripts\week6_duy_prediction_results.json
Found 10 prediction log payloads

=== Preview (first 3 payloads) ===
  [1] doc_dataflow_technical_report
      predicted_label  = report
      confidence_score = 0.4184
      status           = needs_review
  [2] doc_dataflow_technical_report_intro_pages
      predicted_label  = contract
      confidence_score = 0.6096
      status           = accepted
  [3] doc_dataflow_technical_report_architecture_page
      predicted_label  = contract
      confidence_score = 0.6128
      status           = accepted
  ... and 7 more

Connecting to PostgreSQL: datavision@localhost:5432/datavision_db
Connection established.

=== Inserting 10 rows into prediction_logs ===

  Committed all 10 rows
  ⚠️  9/10 rows could not resolve document_db_id

=== Done ===
Successfully inserted 10 rows
Successfully saved count to: week8\database\outputs\db_validation\prediction_log_counts.json
Connection closed.
[23:52:14] Prediction logs loaded
[23:52:14] --- Running: Step 7/9: Load Lap document chunks (optional) ---
[23:52:14] Command: C:\Users\ACER\AppData\Local\Programs\Python\Python310\python.exe week8\scripts\load_document_pages_to_pgvector.py --document-pages week8\scripts\document_pages.jsonl --document-external-id doc_dataflow_technical_report --chunk-size 512 --overlap 50
C:\Users\ACER\AppData\Local\Programs\Python\Python310\lib\site-packages\torch\cuda\__init__.py:129: UserWarning: CUDA initialization: The NVIDIA driver on your system is too old (found version 11020). Please update your GPU driver by downloading and installing a new version from the URL: http://www.nvidia.com/Download/index.aspx Alternatively, go to: https://pytorch.org to install a PyTorch version that has been compiled with your version of the CUDA driver. (Triggered internally at C:\actions-runner\_work\pytorch\pytorch\builder\windows\pytorch\c10\cuda\CUDAFunctions.cpp:108.)
  return torch._C._cuda_getDeviceCount() > 0
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|██████████████| 103/103 [00:00<00:00, 4806.72it/s]
 Loaded embedding model: sentence-transformers/all-MiniLM-L6-v2
Connected to PostgreSQL with pgvector
Validated existing document_chunks schema for pgvector inserts
 Added 293 chunks to pgvector
{
  "pages_loaded": 36,
  "non_empty_pages": 36,
  "empty_pages_skipped": 0,
  "total_characters": 129028,
  "chunks_created": 293,
  "embeddings_generated": 293,
  "vectors_inserted": 293,
  "insertion_time": 14.902
}
[23:52:59] --- Running: Step 7/9: Test RAG query (optional) ---
[23:52:59] Command: C:\Users\ACER\AppData\Local\Programs\Python\Python310\python.exe week8\database\scripts\test_rag_query.py --query What is the DataFlow pipeline? --document-external-id doc_dataflow_technical_report
Connected to PostgreSQL with pgvector
Validated existing document_chunks schema for pgvector inserts
Resolved document_external_id='doc_dataflow_technical_report' -> documents.id=1
C:\Users\ACER\AppData\Local\Programs\Python\Python310\lib\site-packages\torch\cuda\__init__.py:129: UserWarning: CUDA initialization: The NVIDIA driver on your system is too old (found version 11020). Please update your GPU driver by downloading and installing a new version from the URL: http://www.nvidia.com/Download/index.aspx Alternatively, go to: https://pytorch.org to install a PyTorch version that has been compiled with your version of the CUDA driver. (Triggered internally at C:\actions-runner\_work\pytorch\pytorch\builder\windows\pytorch\c10\cuda\CUDAFunctions.cpp:108.)
  return torch._C._cuda_getDeviceCount() > 0
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|██████████████| 103/103 [00:00<00:00, 5094.08it/s]
 Loaded embedding model: sentence-transformers/all-MiniLM-L6-v2
{
  "question": "What is the DataFlow pipeline?",
  "answer": null,
  "retrieved_context": [
    {
      "chunk_id": "doc_dataflow_technical_report_page_11_chunk_007",
      "document_id": 1,
      "text": " DataFlow provides a pipeline interface that enables users to compose operators into multi-stage data-preparation workflows. A pipeline is represented as an ordered sequence of operators (or a lightweight DAG ), forming an end-to-end execution graph that captures the intended dataflow. Figure 4 illustrates the pipeline API and its core components. The pipeline API adopts a PyTorch [49]-like design in which the __init__() method handles resource allocation and operator configuration, while the () method enco",
      "chunk_text": " DataFlow provides a pipeline interface that enables users to compose operators into multi-stage data-preparation workflows. A pipeline is represented as an ordered sequence of operators (or a lightweight DAG ), forming an end-to-end execution graph that captures the intended dataflow. Figure 4 illustrates the pipeline API and its core components. The pipeline API adopts a PyTorch [49]-like design in which the __init__() method handles resource allocation and operator configuration, while the () method enco",
      "page_number": 11,
      "metadata": {
        "source": "DataFlow_Technical_Report.pdf",
        "file_name": "DataFlow_Technical_Report.pdf",
        "page_number": 11,
        "character_count": 3784,
        "document_external_id": "doc_dataflow_technical_report"
      },
      "score": 0.9005318999448987,
      "similarity_score": 0.9005318999448987
    },
    {
      "chunk_id": "doc_dataflow_technical_report_page_13_chunk_000",
      "document_id": 1,
      "text": "DataFlow Technical Report 13 3000 2500 2000 1500 1000 500 Original Data Pipeline Done Normalized Operator Step selpmaS fo rebmuN Node Type Reasoning (9 OPs) Others Generator Filter Text to SQL (7 OPs) AgenticRAG (4 OPs) Code (5 OPs) Text (25 OPs) Figure5 EvolutionofsamplecountsacrossoperatorstagesinDataFlowpipelines. Allpipelinesstartwith1000input samples. The Text pipeline mainly performs pre-training data filtering, and the Code pipeline focuses on expanding code capabilities based on existing instruction",
      "chunk_text": "DataFlow Technical Report 13 3000 2500 2000 1500 1000 500 Original Data Pipeline Done Normalized Operator Step selpmaS fo rebmuN Node Type Reasoning (9 OPs) Others Generator Filter Text to SQL (7 OPs) AgenticRAG (4 OPs) Code (5 OPs) Text (25 OPs) Figure5 EvolutionofsamplecountsacrossoperatorstagesinDataFlowpipelines. Allpipelinesstartwith1000input samples. The Text pipeline mainly performs pre-training data filtering, and the Code pipeline focuses on expanding code capabilities based on existing instruction",
      "page_number": 13,
      "metadata": {
        "source": "DataFlow_Technical_Report.pdf",
        "file_name": "DataFlow_Technical_Report.pdf",
        "page_number": 13,
        "character_count": 3006,
        "document_external_id": "doc_dataflow_technical_report"
      },
      "score": 0.8912520110607147,
      "similarity_score": 0.8912520110607147
    },
    {
      "chunk_id": "doc_dataflow_technical_report_page_7_chunk_002",
      "document_id": 1,
      "text": "ines instantiated from these operators consistently yield strong downstream gains, andevensimplemixturesofdataproducedbydifferentpipelinesremainhighlyeffective. Moreover,thesystem adopts a modular, PyTorch-style \u201cbuilding-block\u201d design with lightweight, well-defined interfaces, making it natural for data agents to compose, orchestrate, and invoke data-processing pipelines programmatically. 3 DataFlow System Overview In this section, we present a overview of DataFlow a unified and automated system that stand",
      "chunk_text": "ines instantiated from these operators consistently yield strong downstream gains, andevensimplemixturesofdataproducedbydifferentpipelinesremainhighlyeffective. Moreover,thesystem adopts a modular, PyTorch-style \u201cbuilding-block\u201d design with lightweight, well-defined interfaces, making it natural for data agents to compose, orchestrate, and invoke data-processing pipelines programmatically. 3 DataFlow System Overview In this section, we present a overview of DataFlow a unified and automated system that stand",
      "page_number": 7,
      "metadata": {
        "source": "DataFlow_Technical_Report.pdf",
        "file_name": "DataFlow_Technical_Report.pdf",
        "page_number": 7,
        "character_count": 3321,
        "document_external_id": "doc_dataflow_technical_report"
      },
      "score": 0.8770944104846967,
      "similarity_score": 0.8770944104846967
    },
    {
      "chunk_id": "doc_dataflow_technical_report_page_35_chunk_000",
      "document_id": 1,
      "text": "DataFlow Technical Report 35 Appendix A Author Contributions \u2022 Hao Liang: Project Leader, Project Founder; algorithm lead and manuscript writing. \u2022 Xiaochen Ma: Project Leader, Project Founder; system lead and manuscript writing. \u2022 Zhou Liu: Project Leader, Project Founder; DataFlow-Agent lead and manuscript writing. \u2022 Zhen Hao Wong: Core Contributor, Project Founder; designs and develops reasoning pipelines, AI4S pipelines, and AgenticRAG pipelines. \u2022 Zhengyang Zhao: Core Contributor, Project Founder; desi",
      "chunk_text": "DataFlow Technical Report 35 Appendix A Author Contributions \u2022 Hao Liang: Project Leader, Project Founder; algorithm lead and manuscript writing. \u2022 Xiaochen Ma: Project Leader, Project Founder; system lead and manuscript writing. \u2022 Zhou Liu: Project Leader, Project Founder; DataFlow-Agent lead and manuscript writing. \u2022 Zhen Hao Wong: Core Contributor, Project Founder; designs and develops reasoning pipelines, AI4S pipelines, and AgenticRAG pipelines. \u2022 Zhengyang Zhao: Core Contributor, Project Founder; desi",
      "page_number": 35,
      "metadata": {
        "source": "DataFlow_Technical_Report.pdf",
        "file_name": "DataFlow_Technical_Report.pdf",
        "page_number": 35,
        "character_count": 2599,
        "document_external_id": "doc_dataflow_technical_report"
      },
      "score": 0.8662717720108175,
      "similarity_score": 0.8662717720108175
    },
    {
      "chunk_id": "doc_dataflow_technical_report_page_5_chunk_001",
      "document_id": 1,
      "text": "and reliable navigation. Beyond the core library, operators, prompt templates, and pipelines can be developed outside the main repository and packaged as standalone Python modules, enabling practitioners to publish and reuse domain-specific components as first-class DataFlow-Extensions. To support this ecosystem, DataFlow includes a Command-Line Interface (CLI) toolchain that scaffolds new extension packages, from operator stubs to full pipeline repositories, standardizing development practices and lowering",
      "chunk_text": "and reliable navigation. Beyond the core library, operators, prompt templates, and pipelines can be developed outside the main repository and packaged as standalone Python modules, enabling practitioners to publish and reuse domain-specific components as first-class DataFlow-Extensions. To support this ecosystem, DataFlow includes a Command-Line Interface (CLI) toolchain that scaffolds new extension packages, from operator stubs to full pipeline repositories, standardizing development practices and lowering",
      "page_number": 5,
      "metadata": {
        "source": "DataFlow_Technical_Report.pdf",
        "file_name": "DataFlow_Technical_Report.pdf",
        "page_number": 5,
        "character_count": 4461,
        "document_external_id": "doc_dataflow_technical_report"
      },
      "score": 0.8616974569378775,
      "similarity_score": 0.8616974569378775
    }
  ],
  "citations": [
    {
      "file_name": "DataFlow_Technical_Report.pdf",
      "page_number": 11,
      "chunk_id": "doc_dataflow_technical_report_page_11_chunk_007",
      "similarity": 0.9005318999448987,
      "document_external_id": "doc_dataflow_technical_report",
      "document_db_id": 1
    },
    {
      "file_name": "DataFlow_Technical_Report.pdf",
      "page_number": 13,
      "chunk_id": "doc_dataflow_technical_report_page_13_chunk_000",
      "similarity": 0.8912520110607147,
      "document_external_id": "doc_dataflow_technical_report",
      "document_db_id": 1
    },
    {
      "file_name": "DataFlow_Technical_Report.pdf",
      "page_number": 7,
      "chunk_id": "doc_dataflow_technical_report_page_7_chunk_002",
      "similarity": 0.8770944104846967,
      "document_external_id": "doc_dataflow_technical_report",
      "document_db_id": 1
    },
    {
      "file_name": "DataFlow_Technical_Report.pdf",
      "page_number": 35,
      "chunk_id": "doc_dataflow_technical_report_page_35_chunk_000",
      "similarity": 0.8662717720108175,
      "document_external_id": "doc_dataflow_technical_report",
      "document_db_id": 1
    },
    {
      "file_name": "DataFlow_Technical_Report.pdf",
      "page_number": 5,
      "chunk_id": "doc_dataflow_technical_report_page_5_chunk_001",
      "similarity": 0.8616974569378775,
      "document_external_id": "doc_dataflow_technical_report",
      "document_db_id": 1
    }
  ],
  "status": "retrieval_only",
  "model": "all-MiniLM-L6-v2",
  "metadata": {
    "latency_ms": 255.34,
    "num_chunks_retrieved": 5,
    "document_id": 1,
    "log_id": 1
  }
}

Logged to rag_query_logs with id=1

--- Generating Validation JSON ---
Successfully saved RAG validation counts to: week8\database\outputs\db_validation\rag_pgvector_counts.json
[23:53:17] --- Running: Step 8/9: Run validation queries ---
[23:53:17] Command: psql -h localhost -p 5432 -U datavision -d datavision_db -v ON_ERROR_STOP=1 -f week8\database\validation\validation_queries_v3.sql
 issue | required_table                                                 
-------+----------------
(0 rows)


 issue | required_view                                                  
-------+---------------
(0 rows)


 orphaned_pages                                                         
----------------
              0
(1 row)


 orphaned_chunks                                                        
-----------------
               0
(1 row)


 orphaned_records                                                       
------------------
                0
(1 row)


 missing_embeddings                                                     
--------------------
                  0
(1 row)


 invalid_vector_dimensions                                              
---------------------------
                         0
(1 row)


 missing_retrieved_chunks                                               
--------------------------
                        0
(1 row)


 empty_chunk_text                                                       
------------------
                0
(1 row)


 missing_run_id_logs                                                    
---------------------
                   0
(1 row)


 invalid_status_logs                                                    
---------------------
                   0
(1 row)


 missing_confidence_scores                                              
---------------------------
                         0
(1 row)


 dashboard_overview_rows                                                
-------------------------
                       1
(1 row)


 name | duplicate_count                                                 
------+-----------------
(0 rows)


 missing_external_id                                                    
---------------------
                   0
(1 row)


 missing_data_quality_score                                             
----------------------------
                          0
(1 row)


 invalid_prediction_status                                              
---------------------------
                         0
(1 row)


 out_of_bounds_confidence                                               
--------------------------
                        0
(1 row)


 math_mismatch_logs                                                     
--------------------
                  0
(1 row)


 stuck_pipelines                                                        
-----------------
               0
(1 row)


 invalid_time_logic                                                     
--------------------
                  0
(1 row)


 extname                                                                
---------
 vector
(1 row)


 orphaned_predictions                                                   
----------------------
                    0
(1 row)


 predictions_needing_review | rows_in_queue_view                        
----------------------------+--------------------
                          4 |                  5
(1 row)


 total_rag_logs | rows_in_rag_metrics_view                              
----------------+--------------------------
              1 |                        1
(1 row)


[23:53:18] Validation passed
[23:53:18] --- Running: Step 9/9: Export dashboard view samples ---
[23:53:18] Command: C:\Users\ACER\AppData\Local\Programs\Python\Python310\python.exe week8\database\scripts\export_dashboard_views.py
Connected to database successfully.

Exporting data from v_dashboard_overview...
  -> Saved 1 rows to week8/database/outputs/dashboard_view_samples\v_dashboard_overview.json
Exporting data from v_latest_ingestion_runs...
  -> Saved 4 rows to week8/database/outputs/dashboard_view_samples\v_latest_ingestion_runs.json
Exporting data from v_data_quality_dashboard...
  -> Saved 4 rows to week8/database/outputs/dashboard_view_samples\v_data_quality_dashboard.json
Exporting data from v_source_quality_summary...
  -> Saved 4 rows to week8/database/outputs/dashboard_view_samples\v_source_quality_summary.json
Exporting data from v_source_quality_detail...
  -> Saved 4 rows to week8/database/outputs/dashboard_view_samples\v_source_quality_detail.json
Exporting data from v_document_rag_readiness...
  -> Saved 1 rows to week8/database/outputs/dashboard_view_samples\v_document_rag_readiness.json
Exporting data from v_prediction_review_queue...
  -> Saved 5 rows to week8/database/outputs/dashboard_view_samples\v_prediction_review_queue.json
Exporting data from v_prediction_confidence_summary...
  -> Saved 4 rows to week8/database/outputs/dashboard_view_samples\v_prediction_confidence_summary.json
Exporting data from v_rag_daily_metrics...
  -> Saved 1 rows to week8/database/outputs/dashboard_view_samples\v_rag_daily_metrics.json
Exporting data from v_recent_activity...
  -> Saved 5 rows to week8/database/outputs/dashboard_view_samples\v_recent_activity.json
Exporting data from v_document_quality_summary...
  -> Saved 1 rows to week8/database/outputs/dashboard_view_samples\v_document_quality_summary.json
Exporting data from v_ingestion_health...
  -> Saved 1 rows to week8/database/outputs/dashboard_view_samples\v_ingestion_health.json

All dashboard view samples exported successfully!
[23:53:18] Dashboard samples exported
[23:53:18] ======================================================================
[23:53:18] Week 8 database setup completed successfully.
[23:53:18] Phat's database is reproducible from zero and ready for CI.
[23:53:18] ======================================================================