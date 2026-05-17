import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _reset_db_engine_between_tests():
    from app.db import reset_engine_for_tests

    reset_engine_for_tests()
    os.environ.pop("DATABASE_URL", None)
    yield
    reset_engine_for_tests()
    os.environ.pop("DATABASE_URL", None)
