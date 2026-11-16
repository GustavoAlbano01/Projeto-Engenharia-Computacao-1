"""Espectrograma (T29 - RF006)."""
import numpy as np

from app.dsp.spectrogram import (MAX_COLUNAS, numero_br, spectrogram_db,
                                 spectrogram_png)

FS = 44100


def test_tom_que_muda_de_frequencia():
    """440 Hz no 1º segundo e 2000 Hz no 2º: o pico de cada coluna acompanha."""
    t = np.arange(2 * FS) / FS
    x = 0.5 * np.where(t < 1, np.sin(2 * np.pi * 440 * t),
                       np.sin(2 * np.pi * 2000 * t))
    tempos, freqs, db = spectrogram_db(x, FS, 1024, "hanning")
    df = FS / 1024
    inicio = freqs[np.argmax(db[tempos < 0.9], axis=1)]
    fim = freqs[np.argmax(db[tempos > 1.1], axis=1)]
    assert np.all(np.abs(inicio - 440) <= df)
    assert np.all(np.abs(fim - 2000) <= df)


def test_dimensoes_e_eixos():
    x = np.zeros(10 * 1024)
    tempos, freqs, db = spectrogram_db(x, FS, 1024, "hamming")
    assert db.shape == (10, 513)              # 10 blocos sucessivos x N/2+1
    assert freqs[-1] == FS / 2                # vai até Nyquist
    assert db.min() >= -120                   # piso em dB (silêncio)


def test_audio_longo_limita_colunas():
    x = np.zeros(5000 * 512)
    tempos, _, db = spectrogram_db(x, FS, 512, "hanning")
    assert len(tempos) == MAX_COLUNAS
    assert np.all(np.diff(tempos) > 0)        # continua em ordem no tempo


def test_png_valido():
    png = spectrogram_png(np.zeros(4096), FS, 1024, "hanning", "teste")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"    # assinatura de todo arquivo PNG

def test_numeros_no_padrao_brasileiro():
    """NF001: os eixos da imagem usam vírgula decimal e ponto de milhar."""
    assert numero_br(0) == "0"
    assert numero_br(0.5) == "0,5"
    assert numero_br(0.05) == "0,05"
    assert numero_br(2500) == "2.500"
    assert numero_br(22050) == "22.050"
    assert numero_br(-20) == "-20"
    assert numero_br(1234567.5) == "1.234.567,5"