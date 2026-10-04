"""Testes dos modelos do banco (T09). Usam SQLite em memória."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import create_tables, make_engine, make_session_factory
from app.models import Analysis, Audio


@pytest.fixture
def session():
    engine = make_engine("sqlite:///:memory:")
    create_tables(engine)
    with make_session_factory(engine)() as s:
        yield s
    engine.dispose()


def new_audio(**overrides):
    data = dict(filename="tom_440hz.wav", stored_path="uploads/1.wav",
                bits_per_sample=16, sample_rate_hz=44100, channels=1,
                num_samples=132300, size_bytes=264644)
    data.update(overrides)
    return Audio(**data)


def new_analysis(audio, block_size=1024):
    return Analysis(audio=audio, block_size=block_size, window="hanning",
                    blocks_used=256, magnitudes=[0.0] * (block_size // 2 + 1),
                    peak_bin=10, peak_frequency_hz=430.66,
                    peak_magnitude=0.485)


def test_cria_audio_com_valores_padrao(session):
    audio = new_audio()
    session.add(audio)
    session.commit()
    assert audio.id is not None
    assert audio.format == "wav_pcm"
    assert audio.uploaded_at is not None
    assert audio.duration_s == pytest.approx(3.0)


def test_analise_guarda_vetor_e_calcula_frequencias(session):
    analysis = new_analysis(new_audio())
    analysis.magnitudes[10] = 0.485
    session.add(analysis)
    session.commit()
    session.expunge_all()  # força reler do banco, não da memória

    lida = session.get(Analysis, analysis.id)
    assert len(lida.magnitudes) == 513
    assert lida.magnitudes[10] == pytest.approx(0.485)
    assert lida.warnings == []
    assert lida.freq_resolution_hz == pytest.approx(44100 / 1024)
    assert len(lida.frequencies_hz) == len(lida.magnitudes)
    assert lida.frequencies_hz[10] == pytest.approx(430.664, abs=1e-3)


def test_analise_sem_audio_existente_e_recusada(session):
    session.add(Analysis(audio_id=999, block_size=512, window="hamming",
                         blocks_used=1, magnitudes=[0.0] * 257, peak_bin=1,
                         peak_frequency_hz=86.13, peak_magnitude=0.1))
    with pytest.raises(IntegrityError):
        session.commit()


def test_excluir_analise_mantem_audio(session):
    audio = new_audio()
    analysis = new_analysis(audio)
    session.add(analysis)
    session.commit()
    session.delete(analysis)
    session.commit()
    assert session.get(Audio, audio.id) is not None
    assert session.scalars(select(Analysis)).all() == []


def test_excluir_audio_apaga_suas_analises(session):
    audio = new_audio()
    session.add_all([new_analysis(audio), new_analysis(audio, 2048)])
    session.commit()
    session.delete(audio)
    session.commit()
    assert session.scalars(select(Analysis)).all() == []


def test_historico_ordenado_do_mais_recente(session):
    audio = new_audio()
    primeira, segunda = new_analysis(audio), new_analysis(audio, 2048)
    primeira.created_at = datetime(2026, 10, 1, tzinfo=timezone.utc)
    segunda.created_at = datetime(2026, 10, 2, tzinfo=timezone.utc)
    session.add_all([segunda, primeira])  # ordem de inserção trocada
    session.commit()
    ids = session.scalars(
        select(Analysis.id).order_by(Analysis.created_at.desc())).all()
    assert ids == [segunda.id, primeira.id]


def test_script_init_db_cria_o_arquivo(tmp_path, monkeypatch):
    import init_db
    from app import database

    db_file = tmp_path / "instance" / "aea.db"
    monkeypatch.setattr(init_db, "DB_PATH", db_file)
    monkeypatch.setattr(init_db, "make_engine",
                        lambda: database.make_engine(f"sqlite:///{db_file}"))
    assert init_db.main([]) == 0
    assert db_file.exists()
