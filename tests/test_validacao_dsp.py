"""Validação do núcleo DSP com sinais conhecidos (T19 - RF003, RF010).

Caminho completo, igual ao do sistema:
gerar_sinais (T10) -> WAV -> read_wav (T11) -> analyze (T20).
O numpy não é usado para calcular nenhum espectro aqui.
"""
import wave

import numpy as np
import pytest

from app.dsp.analysis import analyze
from app.dsp.dft import dft
from app.dsp.fft import fft
from app.dsp.wav_reader import read_wav
from tools.gerar_sinais import gerar_amostras, salvar_wav

TAXAS = (8000, 22050, 44100, 48000)
N = 1024


def wav_de_tons(tmp_path, freqs, amps, taxa, duracao_s=3.0):
    """Gera o WAV com o gerador do T10 e lê com o leitor do T11."""
    caminho = tmp_path / "sinal.wav"
    salvar_wav(caminho, gerar_amostras(freqs, amps, taxa, duracao_s), taxa)
    return read_wav(str(caminho))


def mag_na_freq(resultado, freq_hz):
    """Magnitude no bin mais próximo de 'freq_hz'."""
    df = resultado["freq_resolution_hz"]
    return resultado["magnitudes"][round(freq_hz / df)]


# ---------- 1. Tom puro em várias taxas ----------
@pytest.mark.parametrize("taxa", TAXAS)
@pytest.mark.parametrize("freq", (440.0, 1000.0))
def test_tom_puro_pico_dentro_de_um_bin(tmp_path, taxa, freq):
    wav = wav_de_tons(tmp_path, (freq,), (0.5,), taxa)
    r = analyze(wav.samples, wav.sample_rate_hz, N, "hanning")
    df = taxa / N
    assert abs(r["peak"]["frequency_hz"] - freq) <= df
    assert r["peak"]["magnitude"] == pytest.approx(0.5, abs=0.08)


# ---------- 2. Dois tons ----------
@pytest.mark.parametrize("taxa", TAXAS)
def test_dois_tons_aparecem(tmp_path, taxa):
    wav = wav_de_tons(tmp_path, (440.0, 1000.0), (0.4, 0.4), taxa)
    r = analyze(wav.samples, wav.sample_rate_hz, N, "hanning")
    for freq in (440.0, 1000.0):
        assert 0.3 <= mag_na_freq(r, freq) <= 0.45     # cada tom ≈ 0,4
    assert mag_na_freq(r, 700.0) < 0.01                 # entre eles: quase nada


# ---------- 3. Comparação de janelas ----------
def test_janelas_reduzem_vazamento():
    """Tom no meio dos bins 10 e 11: pior caso de vazamento."""
    fs = 44100
    freq = 10.5 * fs / N
    t = np.arange(2 * fs) / fs
    x = 0.5 * np.sin(2 * np.pi * freq * t)

    longe = {}  # magnitude 30 bins longe do tom
    for janela in ("rectangular", "hanning", "hamming"):
        longe[janela] = analyze(x, fs, N, janela)["magnitudes"][40]

    assert longe["hanning"] < longe["rectangular"] / 100
    assert longe["hamming"] < longe["rectangular"] / 2


def test_hanning_perde_menos_amplitude_que_retangular():
    """No pior caso (meio do bin), a Hanning mede o tom mais perto de A."""
    fs = 44100
    freq = 10.5 * fs / N
    t = np.arange(2 * fs) / fs
    x = 0.5 * np.sin(2 * np.pi * freq * t)
    ret = analyze(x, fs, N, "rectangular")["peak"]["magnitude"]
    han = analyze(x, fs, N, "hanning")["peak"]["magnitude"]
    assert ret == pytest.approx(0.318, abs=0.01)   # 0,5 · 2/π
    assert han == pytest.approx(0.425, abs=0.01)
    assert han > ret


# ---------- 4. Estéreo -> mono ----------
def test_estereo_vira_mono_pela_media(tmp_path):
    """Tom de amplitude 0,5 só no canal esquerdo: a média dá 0,25."""
    fs = 44100
    esquerdo = gerar_amostras((1000.0,), (0.5,), fs, 2.0)
    direito = np.zeros_like(esquerdo)
    pcm = np.round(np.column_stack([esquerdo, direito]) * 32767).astype("<i2")

    caminho = tmp_path / "estereo.wav"
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(fs)
        w.writeframes(pcm.tobytes())    # L R L R ... intercalado

    wav = read_wav(str(caminho))
    assert wav.channels == 2
    r = analyze(wav.samples, wav.sample_rate_hz, N, "hanning")
    assert abs(r["peak"]["frequency_hz"] - 1000) <= fs / N
    assert r["peak"]["magnitude"] == pytest.approx(0.25, abs=0.04)


# ---------- 5. DFT = FFT num bloco real ----------
def test_dft_e_fft_iguais_em_bloco_de_wav(tmp_path):
    wav = wav_de_tons(tmp_path, (440.0, 1000.0), (0.4, 0.4), 8000, 1.0)
    bloco = wav.samples[:512]
    np.testing.assert_allclose(fft(bloco), dft(bloco), atol=1e-9)