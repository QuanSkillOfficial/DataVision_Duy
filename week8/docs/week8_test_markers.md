Custom markers are defined in the `pytest.ini` file located at the root of the project to categorize the test suite based on infrastructure dependencies.

PS D:\Quansolution\Week> pytest week8/database/tests -v                
============================= test session starts =============================
platform win32 -- Python 3.10.5, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ACER\AppData\Local\Programs\Python\Python310\python.exe
rootdir: D:\Quansolution\Week
configfile: pytest.ini
plugins: anyio-4.14.1, Faker-40.12.0
collected 22 items                                                             

week8/database/tests/integration/test_backup_restore_gates.py::test_backup_is_non_empty_and_readable PASSED [  4%]
week8/database/tests/integration/test_backup_restore_gates.py::test_restore_preserves_pgvector PASSED [  9%]
week8/database/tests/integration/test_backup_restore_gates.py::test_restore_counts_match PASSED [ 13%]
week8/database/tests/integration/test_data_lifecycle.py::test_migration_does_not_load_demo_data PASSED [ 18%]
week8/database/tests/integration/test_data_lifecycle.py::test_reference_data_seed_is_idempotent PASSED [ 22%]
week8/database/tests/integration/test_data_lifecycle.py::test_reference_data_change_is_applied_not_skipped PASSED [ 27%]
week8/database/tests/integration/test_data_lifecycle.py::test_staging_can_skip_demo_data PASSED [ 31%]
week8/database/tests/integration/test_data_lifecycle.py::test_seed_second_run_has_no_duplicates PASSED [ 36%]
week8/database/tests/integration/test_data_lifecycle.py::test_runtime_data_not_overwritten_by_reseed PASSED [ 40%]
week8/database/tests/integration/test_migrations.py::test_migration_fresh_install PASSED [ 45%]
week8/database/tests/integration/test_migrations.py::test_migration_upgrade_from_week7 PASSED [ 50%]
week8/database/tests/integration/test_migrations.py::test_migration_second_run_is_noop PASSED [ 54%]
week8/database/tests/integration/test_migrations.py::test_destructive_migration_is_blocked PASSED [ 59%]
week8/database/tests/integration/test_migrations.py::test_backup_failure_blocks_setup PASSED [ 63%]
week8/database/tests/integration/test_migrations.py::test_backup_manifest_contains_row_counts PASSED [ 68%]
week8/database/tests/integration/test_migrations.py::test_restore_into_disposable_database PASSED [ 72%]
week8/database/tests/live/test_stagging_db.py::test_live_database_requires_explicit_flag SKIPPED [ 77%]
week8/database/tests/live/test_stagging_db.py::test_live_database_is_reachable_and_has_core_tables SKIPPED [ 81%]
week8/database/tests/unit/test_congif.py::test_core_tables_and_views_are_well_formed PASSED [ 86%]
week8/database/tests/unit/test_congif.py::test_get_db_connection_requires_db_password PASSED [ 90%]
week8/database/tests/unit/test_congif.py::test_get_db_connection_defaults PASSED [ 95%]
week8/database/tests/unit/test_congif.py::test_should_skip_demo_data_reads_env_flag PASSED [100%]

======================= 20 passed, 2 skipped in 17.72s ========================