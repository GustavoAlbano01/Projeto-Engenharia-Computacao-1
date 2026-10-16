"""Testes do leitor de WAV (T11)."""
import io
import struct
import wave

import numpy as np
import pytest

from app.dsp.wav_reader import (EmptyAudioError, InvalidWavError,
                                UnsupportedFormatError, read_wav)
from tools.gerar_sinais import gerar_todos


def wav_bytes(frames, channels=1, sample_width=2, rate=8000):
    """Monta um WAV em memória a partir de uma lista de inteiros."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(rate)
        fmt = {1: "b", 2: "h", 3: None}[sample_width]
        if fmt:
            w.writeframes(struct.pack(f"<{len(frames)}{fmt}", *frames))
        else:
            w.writeframes(bytes(3 * len(frames)))
    buf.seek(0)
    return buf

def test_le_mono_com_metadados():
    audio = read_wav(wav_bytes([0, 16384, -16384, 32767], rate=8000))
    assert audio.channels == 1
    assert audio.sample_rate_hz == 8000
    assert audio.num_samples == 4
    assert audio.duration_s == pytest.approx(4 / 8000)
    assert audio.samples.tolist() == pytest.approx(
        [0, 0.5, -0.5, 32767 / 32768])

def test_estereo_vira_mono_pela_media():
    # quadros (L, R): (10000, 20000) e (-32768, 0)
    audio = read_wav(wav_bytes([10000, 20000, -32768, 0], channels=2))
    assert audio.channels == 2
    assert audio.num_samples == 2          # por canal
    assert audio.samples.tolist() == pytest.approx(
        [15000 / 32768, -16384 / 32768])

def test_metadados_no_formato_do_contrato():
    meta = read_wav(wav_bytes([0] * 132300, rate=44100)).metadata()
    assert meta == {"format": "wav_pcm", "bits_per_sample": 16,
                    "sample_rate_hz": 44100, "channels": 1,
                    "num_samples": 132300, "duration_s": 3.0}


def test_le_os_sinais_do_gerador_t10(tmp_path):
    gerar_todos(tmp_path, (44100,), 1.0)
    audio = read_wav(str(tmp_path / "tom_440hz_44100.wav"))
    assert audio.num_samples == 44100
    assert np.abs(audio.samples).max() == pytest.approx(0.5, abs=1e-3)

def test_recusa_8_bits():
    with pytest.raises(UnsupportedFormatError):
        read_wav(wav_bytes([0, 1, 2], sample_width=1))


def test_recusa_24_bits():
    with pytest.raises(UnsupportedFormatError):
        read_wav(wav_bytes([0, 0], sample_width=3))


def test_recusa_wav_ponto_flutuante():
    # cabeçalho com formato 3 (IEEE float) em vez de 1 (PCM)
    fmt = struct.pack("<HHIIHH", 3, 1, 8000, 32000, 4, 32)
    data = bytes(8)
    corpo = (b"WAVE" + b"fmt " + struct.pack("<I", 16) + fmt
             + b"data" + struct.pack("<I", len(data)) + data)
    arquivo = io.BytesIO(b"RIFF" + struct.pack("<I", len(corpo)) + corpo)
    with pytest.raises(UnsupportedFormatError):
        read_wav(arquivo)

def test_recusa_arquivo_que_nao_e_wav():
    with pytest.raises(InvalidWavError):
        read_wav(io.BytesIO(b"ID3 isto parece um mp3" * 10))


def test_recusa_arquivo_truncado():
    with pytest.raises(InvalidWavError):
        read_wav(io.BytesIO(b"RIFF\x24\x00"))


def test_recusa_wav_sem_amostras():
    with pytest.raises(EmptyAudioError):
        read_wav(wav_bytes([]))


def test_codigos_de_erro_do_contrato():
    assert InvalidWavError.code == "INVALID_WAV"
    assert UnsupportedFormatError.code == "UNSUPPORTED_FORMAT"
    assert EmptyAudioError.code == "EMPTY_AUDIO"