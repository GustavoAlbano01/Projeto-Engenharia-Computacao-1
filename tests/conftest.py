import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    # Uploads vão para uma pasta temporária, não para backend/uploads/.
    return create_app(upload_dir=tmp_path / "uploads").test_client()
