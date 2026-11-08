import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    # Uploads numa pasta temporária e banco em memória:
    # os testes nunca mexem nos dados reais.
    app = create_app(upload_dir=tmp_path / "uploads",
                     db_url="sqlite:///:memory:")
    return app.test_client()
