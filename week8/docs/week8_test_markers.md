Custom markers are defined in the `pytest.ini` file located at the root of the project to categorize the test suite based on infrastructure dependencies.

```ini
[pytest]
markers =
    unit: Pure logic tests, no database connection required.
    integration: Requires a migrated and seeded local/CI database.
    live_db: Connects to the real staging database. Requires DATABASE_LIVE_TEST=1.


week8/database/tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   └── test_config.py
├── integration/
│   ├── __init__.py
│   └── test_migrations.py
└── live/
    ├── __init__.py
    └── test_staging_db.py

PS D:\Quansolution\Week> pytest week8/database/tests/ --collect-only
============================= test session starts =============================
platform win32 -- Python 3.10.5, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Quansolution\Week
plugins: anyio-4.14.1, Faker-40.12.0
collected 3 items                                                              

<Dir Week>
  <Dir week8>
    <Dir database>
      <Package tests>
        <Package integration>
          <Module test_migrations.py>
            <Function test_dummy_integration>
        <Package live>
          <Module test_stagging_db.py>
            <Function test_dummy_live>
        <Package unit>
          <Module test_congif.py>
            <Function test_dummy_unit>

========================= 3 tests collected in 0.04s ==========================