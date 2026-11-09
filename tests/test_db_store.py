"""Testes do DbStore (T20). Usam SQLite em memória."""
import re

import pytest

from app.database import create_tables, make_engine, make_session_factory
from app.db_store import DbStore

METADATA = {"format": "wav_pcm", "bits_per_sample": 16,
            "sample_rate_hz": 44100, "channels": 1,
            "num_samples": 132300, "duration_s": 3.0}

RESULT = {  # formato de dsp.analysis.analyze(), com vetores pequenos
    "params": {"block_size": 4, "window": "hanning"},
    "blocks_used": 256,
    "freq_resolution_hz": 11025.0,
    "frequencies_hz": [0.0, 11025.0, 22050.0],
    "magnitudes": [0.0, 0.5, 0.1],
    "peak": {"bin": 1, "frequency_hz": 11025.0, "magnitude": 0.5},
    "warnings": [],
}

ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


@pytest.fixture
def store():
    engine = make_engine("sqlite:///:memory:")
    create_tables(engine)
    yield DbStore(make_session_factory(engine))
    engine.dispose()


def add_audio(store, filename="tom_440hz.wav"):
    return store.add_audio(filename, 264644, METADATA, "uploads/x.wav")


# ---------- áudios ----------
def test_add_audio_formato_do_contrato(store):
    audio = add_audio(store)
    assert audio["id"] == 1
    assert audio["filename"] == "tom_440hz.wav"
    assert audio["duration_s"] == 3.0
    assert ISO_UTC.match(audio["uploaded_at"])


def test_get_audio_e_caminho(store):
    audio = add_audio(store)
    assert store.get_audio(audio["id"]) == audio
    assert store.get_audio_path(audio["id"]) == "uploads/x.wav"


def test_audio_inexistente(store):
    assert store.get_audio(999) is None
    assert store.get_audio_path(999) is None


# ---------- análises ----------
def test_add_analysis_formato_do_contrato(store):
    audio = add_audio(store)
    a = store.add_analysis(audio["id"], RESULT)
    assert a["audio"] == {"id": audio["id"], "filename": "tom_440hz.wav"}
    assert a["params"] == {"block_size": 4, "window": "hanning"}
    assert a["magnitudes"] == [0.0, 0.5, 0.1]
    assert len(a["frequencies_hz"]) == len(a["magnitudes"])
    assert a["peak"]["bin"] == 1
    assert ISO_UTC.match(a["created_at"])


def test_get_analysis_igual_ao_criado(store):
    audio = add_audio(store)
    created = store.add_analysis(audio["id"], RESULT)
    assert store.get_analysis(created["id"]) == created


def test_historico_mais_recente_primeiro_e_sem_vetores(store):
    audio = add_audio(store)
    first = store.add_analysis(audio["id"], RESULT)
    second = store.add_analysis(audio["id"], RESULT)
    summaries = store.list_summaries()
    assert [s["id"] for s in summaries] == [second["id"], first["id"]]
    assert "magnitudes" not in summaries[0]


def test_historico_vazio(store):
    assert store.list_summaries() == []


def test_delete_analysis(store):
    audio = add_audio(store)
    a = store.add_analysis(audio["id"], RESULT)
    assert store.delete_analysis(a["id"]) is True
    assert store.get_analysis(a["id"]) is None
    assert store.delete_analysis(a["id"]) is False   # já não existe