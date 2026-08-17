import os
import pytest


def pytest_collection_modifyitems(config, items):
    live_enabled = os.environ.get("RUN_LIVE_DB_TESTS", "").strip().lower() in (
        "1", "true", "yes",
    )
    if live_enabled:
        return

    skip_live = pytest.mark.skip(
        reason="live_db tests require RUN_LIVE_DB_TESTS=1 (explicit opt-in); "
               "they never run by default to avoid touching staging/production."
    )
    for item in items:
        if "live_db" in item.keywords:
            item.add_marker(skip_live)