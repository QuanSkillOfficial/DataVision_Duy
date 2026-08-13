## Output: week8\database\outputs\db_validation\restore_result.json
PS D:\Quansolution\Week> $LatestDump = Get-ChildItem -Path "week8\database\outputs\backups\*.dump" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
>> Write-Host "=========================================================="
>> Write-Host "The latest dump file (PG16 format) is: $($LatestDump.Name)"
>> Write-Host "=========================================================="
==========================================================
The latest dump file (PG16 format) is: datavision_db_20260813_125022.dump
==========================================================
PS D:\Quansolution\Week> python week8/database/scripts/restore_database.py `    
>>    --dump-file $LatestDump.FullName `                                        
>>    --verify `
>>    --reference-counts week8/database/outputs/backups/backup_manifest.json `
>>    --pg-bin-dir "D:\Postgresql\bin"                                    
[13:12:48] [restore] ======================================================================
[13:12:48] [restore] Week 8 Database Restore Procedure (DV-PHAT-03)
[13:12:48] [restore] Dump file: D:\Quansolution\Week\week8\database\outputs\backups\datavision_db_20260813_125022.dump
[13:12:48] [restore] Target DB: datavision@localhost:5432/datavision_db_restore_test
[13:12:48] [restore] PG Bin Dir: D:\Postgresql\bin
[13:12:48] [restore] ======================================================================
[13:12:48] [restore] --- Verify dump file is readable (pg_restore --list) ---
[13:12:48] [restore] Command: D:\Postgresql\bin\pg_restore --list D:\Quansolution\Week\week8\database\outputs\backups\datavision_db_20260813_125022.dump
[13:12:48] [restore] ;
; Archive created at 2026-08-13 12:50:22
;     dbname: datavision_db
;     TOC Entries: 118
;     Compression: gzip
;     Dump Version: 1.16-0
;     Format: CUSTOM
;     Integer: 4 bytes
;     Offset: 8 bytes
;     Dumped from database version: 16.14 (Debian 16.14-1.pgdg12+1)
;     Dumped by pg_dump version: 17.5
;
;
; Selected TOC Entries:
;
2; 3079 16389 EXTENSION - vector 
3811; 0 0 COMMENT - EXTENSION vector 
230; 1259 76178 TABLE public analytics_events datavision
229; 1259 76177 SEQUENCE public analytics_events_id_seq datavision
3812; 0 0 SEQUENCE OWNED BY public analytics_events_id_seq datavision
224; 1259 76122 TABLE public document_chunks datavision
223; 1259 76121 SEQUENCE public document_chunks_id_seq datavision
3813; 0 0 SEQUENCE OWNED BY public document_chunks_id_seq datavision
236; 1259 76230 TABLE public document_pages datavision
235; 1259 76229 SEQUENCE public document_pages_id_seq datavision
3814; 0 0 SEQUENCE OWNED BY public document_pages_id_seq datavision
222; 1259 76103 TABLE public documents datavision
221; 1259 76102 SEQUENCE public documents_id_seq datavision
3815; 0 0 SEQUENCE OWNED BY public documents_id_seq datavision
228; 1259 76157 TABLE public ingestion_logs datavision
227; 1259 76156 SEQUENCE public ingestion_logs_id_seq datavision
3816; 0 0 SEQUENCE OWNED BY public ingestion_logs_id_seq datavision
220; 1259 76093 TABLE public pipeline_runs datavision
219; 1259 76092 SEQUENCE public pipeline_runs_id_seq datavision
3817; 0 0 SEQUENCE OWNED BY public pipeline_runs_id_seq datavision
234; 1259 76203 TABLE public prediction_logs datavision
233; 1259 76202 SEQUENCE public prediction_logs_id_seq datavision
3818; 0 0 SEQUENCE OWNED BY public prediction_logs_id_seq datavision
232; 1259 76188 TABLE public rag_query_logs datavision
231; 1259 76187 SEQUENCE public rag_query_logs_id_seq datavision
3819; 0 0 SEQUENCE OWNED BY public rag_query_logs_id_seq datavision
216; 1259 76068 TABLE public schema_migrations datavision
218; 1259 76077 TABLE public sources datavision
217; 1259 76076 SEQUENCE public sources_id_seq datavision
3820; 0 0 SEQUENCE OWNED BY public sources_id_seq datavision
226; 1259 76141 TABLE public structured_records datavision
225; 1259 76140 SEQUENCE public structured_records_id_seq datavision
3821; 0 0 SEQUENCE OWNED BY public structured_records_id_seq datavision
237; 1259 76259 VIEW public v_dashboard_overview datavision
245; 1259 76295 VIEW public v_data_quality_dashboard datavision
240; 1259 76273 VIEW public v_document_quality_summary datavision
247; 1259 76305 VIEW public v_document_rag_readiness datavision
238; 1259 76264 VIEW public v_ingestion_health datavision
244; 1259 76290 VIEW public v_latest_ingestion_runs datavision
242; 1259 76281 VIEW public v_prediction_confidence_summary datavision
248; 1259 76310 VIEW public v_prediction_review_queue datavision
241; 1259 76277 VIEW public v_rag_daily_metrics datavision
243; 1259 76285 VIEW public v_recent_activity datavision
246; 1259 76300 VIEW public v_source_quality_detail datavision
239; 1259 76268 VIEW public v_source_quality_summary datavision
3564; 2604 76181 DEFAULT public analytics_events id datavision
3555; 2604 76125 DEFAULT public document_chunks id datavision
3570; 2604 76233 DEFAULT public document_pages id datavision
3552; 2604 76106 DEFAULT public documents id datavision
3562; 2604 76160 DEFAULT public ingestion_logs id datavision
3548; 2604 76096 DEFAULT public pipeline_runs id datavision
3568; 2604 76206 DEFAULT public prediction_logs id datavision
3566; 2604 76191 DEFAULT public rag_query_logs id datavision
3542; 2604 76080 DEFAULT public sources id datavision
3559; 2604 76144 DEFAULT public structured_records id datavision
3798; 0 76178 TABLE DATA public analytics_events datavision
3792; 0 76122 TABLE DATA public document_chunks datavision
3804; 0 76230 TABLE DATA public document_pages datavision
3790; 0 76103 TABLE DATA public documents datavision
3796; 0 76157 TABLE DATA public ingestion_logs datavision
3788; 0 76093 TABLE DATA public pipeline_runs datavision
3802; 0 76203 TABLE DATA public prediction_logs datavision
3800; 0 76188 TABLE DATA public rag_query_logs datavision
3784; 0 76068 TABLE DATA public schema_migrations datavision
3786; 0 76077 TABLE DATA public sources datavision
3794; 0 76141 TABLE DATA public structured_records datavision
3822; 0 0 SEQUENCE SET public analytics_events_id_seq datavision
3823; 0 0 SEQUENCE SET public document_chunks_id_seq datavision
3824; 0 0 SEQUENCE SET public document_pages_id_seq datavision
3825; 0 0 SEQUENCE SET public documents_id_seq datavision
3826; 0 0 SEQUENCE SET public ingestion_logs_id_seq datavision
3827; 0 0 SEQUENCE SET public pipeline_runs_id_seq datavision
3828; 0 0 SEQUENCE SET public prediction_logs_id_seq datavision
3829; 0 0 SEQUENCE SET public rag_query_logs_id_seq datavision
3830; 0 0 SEQUENCE SET public sources_id_seq datavision
3831; 0 0 SEQUENCE SET public structured_records_id_seq datavision
3607; 2606 76186 CONSTRAINT public analytics_events analytics_events_pkey datavision
3594; 2606 76134 CONSTRAINT public document_chunks document_chunks_chunk_id_keydatavision
3596; 2606 76132 CONSTRAINT public document_chunks document_chunks_pkey datavision
3617; 2606 76239 CONSTRAINT public document_pages document_pages_pkey datavision
3588; 2606 76115 CONSTRAINT public documents documents_document_external_id_keydatavision
3590; 2606 76113 CONSTRAINT public documents documents_pkey datavision
3605; 2606 76166 CONSTRAINT public ingestion_logs ingestion_logs_pkey datavision
3586; 2606 76101 CONSTRAINT public pipeline_runs pipeline_runs_pkey datavision
3615; 2606 76213 CONSTRAINT public prediction_logs prediction_logs_pkey datavision
3611; 2606 76196 CONSTRAINT public rag_query_logs rag_query_logs_pkey datavision
3578; 2606 76075 CONSTRAINT public schema_migrations schema_migrations_pkey datavision
3581; 2606 76091 CONSTRAINT public sources sources_name_key datavision
3583; 2606 76089 CONSTRAINT public sources sources_pkey datavision
3600; 2606 76150 CONSTRAINT public structured_records structured_records_pkey datavision
3608; 1259 76255 INDEX public idx_analytics_events_created_at datavision
3597; 1259 76246 INDEX public idx_chunks_document_id datavision
3598; 1259 76249 INDEX public idx_document_chunks_embedding_hnsw datavision
3591; 1259 76251 INDEX public idx_documents_created_at datavision
3592; 1259 76245 INDEX public idx_documents_source_id datavision
3601; 1259 76252 INDEX public idx_ingestion_logs_created_at datavision
3602; 1259 76256 INDEX public idx_ingestion_logs_status datavision
3603; 1259 76247 INDEX public idx_logs_pipeline_id datavision
3618; 1259 76248 INDEX public idx_pages_document_id datavision
3584; 1259 76250 INDEX public idx_pipeline_runs_created_at datavision
3612; 1259 76253 INDEX public idx_prediction_logs_created_at datavision
3613; 1259 76257 INDEX public idx_prediction_logs_status datavision
3609; 1259 76254 INDEX public idx_rag_query_logs_created_at datavision
3579; 1259 76258 INDEX public idx_sources_status datavision
3620; 2606 76135 FK CONSTRAINT public document_chunks document_chunks_document_id_fkey datavision
3628; 2606 76240 FK CONSTRAINT public document_pages document_pages_document_id_fkey datavision
3619; 2606 76116 FK CONSTRAINT public documents documents_source_id_fkey datavision
3622; 2606 76172 FK CONSTRAINT public ingestion_logs ingestion_logs_pipeline_run_id_fkey datavision
3623; 2606 76167 FK CONSTRAINT public ingestion_logs ingestion_logs_source_id_fkey datavision
3625; 2606 76219 FK CONSTRAINT public prediction_logs prediction_logs_document_id_fkey datavision
3626; 2606 76214 FK CONSTRAINT public prediction_logs prediction_logs_source_id_fkey datavision
3627; 2606 76224 FK CONSTRAINT public prediction_logs prediction_logs_structured_record_id_fkey datavision
3624; 2606 76197 FK CONSTRAINT public rag_query_logs rag_query_logs_document_id_fkey datavision
3621; 2606 76151 FK CONSTRAINT public structured_records structured_records_source_id_fkey datavision
[13:12:48] [restore] --- Drop database datavision_db_restore_test (if exists) ---
[13:12:48] [restore] Command: D:\Postgresql\bin\dropdb -h localhost -p 5432 -U datavision --if-exists datavision_db_restore_test
[13:12:48] [restore] --- Create database datavision_db_restore_test ---
[13:12:48] [restore] Command: D:\Postgresql\bin\createdb -h localhost -p 5432 -U datavision datavision_db_restore_test
[13:12:48] [restore] --- pg_restore into datavision_db_restore_test ---
[13:12:48] [restore] Command: D:\Postgresql\bin\pg_restore -h localhost -p 5432-U datavision -d datavision_db_restore_test --no-owner --no-privileges D:\Quansolution\Week\week8\database\outputs\backups\datavision_db_20260813_125022.dump
[13:12:49] [restore] WARNING: pg_restore into datavision_db_restore_test failed(exit 1): pg_restore: error: could not execute query: ERROR:  unrecognized configuration parameter "transaction_timeout"
Command was: SET transaction_timeout = 0;
pg_restore: warning: errors ignored on restore: 1
[13:12:49] [restore] Restore completed.
[13:12:49] [restore] Post-restore counts: {
  "pgvector_extension_present": true,
  "sources": 4,
  "documents": 1,
  "document_pages": 36,
  "document_chunks": 293,
  "structured_records": 11524,
  "ingestion_logs": 4,
  "pipeline_runs": 4,
  "analytics_events": 0,
  "rag_query_logs": 1,
  "prediction_logs": 10,
  "view:v_dashboard_overview": 1,
  "view:v_ingestion_health": 1,
  "view:v_source_quality_summary": 4,
  "view:v_document_quality_summary": 1,
  "view:v_rag_daily_metrics": 1,
  "view:v_prediction_confidence_summary": 4,
  "view:v_recent_activity": 5,
  "view:v_latest_ingestion_runs": 4,
  "view:v_data_quality_dashboard": 4,
  "view:v_source_quality_detail": 4,
  "view:v_document_rag_readiness": 1,
  "view:v_prediction_review_queue": 5
}
[13:12:49] [restore] Row counts match reference. Restore verified.
[13:12:49] [restore] Report written to week8/database/outputs/db_validation/restore_result.json