import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("DATABASE_LIVE_TEST") != "1",
    reason="set DATABASE_LIVE_TEST=1 to run against a real staging DB"
)
def test_dummy_live():
    assert True