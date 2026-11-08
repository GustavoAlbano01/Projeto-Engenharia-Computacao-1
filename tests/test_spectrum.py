"""Testes de magnitude, eixo de frequência e pico (T17).

Usa os tons do gerador de sinais (T10), de frequência conhecida, com a
janela (T14) e a FFT própria (T16).
"""
import numpy as np
import pytest

from app.contract import BLOCK_SIZES, WINDOWS
from app.dsp.fft import fft
from app.dsp.spectrum import (find_peak, freq_resolution, frequencies,
                              magnitude)
from app.dsp.windows import make_window
from tools.gerar_sinais import gerar_amostras

FS = 44100


def espectro_do_tom(freq, amplitude, n, window):
    x = gerar_amostras((freq,), (amplitude,), FS, 1.0)[:n]
    w = make_window(window, n)
    return magnitude(fft(x * w), w)


def test_eixo_de_frequencia_do_contrato():
    f = frequencies(1024, FS)
    assert len(f) == 513
    assert f[0] == 0
    assert f[10] == pytest.approx(430.664, abs=1e-3)
    assert f[-1] == pytest.approx(FS / 2)            # Nyquist
    assert freq_resolution(1024, FS) == pytest.approx(43.0664, abs=1e-4)


@pytest.mark.parametrize("n", BLOCK_SIZES)
@pytest.mark.parametrize("window", WINDOWS)
@pytest.mark.parametrize("freq", (440, 1000))
def test_pico_dentro_de_um_bin(freq, window, n):
    mag = espectro_do_tom(freq, 0.5, n, window)
    pico = find_peak(mag, frequencies(n, FS))
    assert len(mag) == n // 2 + 1
    assert abs(pico["frequency_hz"] - freq) <= FS / n


def test_tom_no_centro_do_bin_da_amplitude_exata():
    n = 1024
    freq = 20 * FS / n                       # cai exatamente no bin 20
    mag = espectro_do_tom(freq, 0.5, n, "rectangular")
    assert mag[20] == pytest.approx(0.5, abs=1e-6)


def test_bin_dc_e_nyquist_nao_dobram():
    n = 8
    mag = magnitude(fft(np.ones(n)), np.ones(n))   # sinal constante = 1
    assert mag[0] == pytest.approx(1)
    assert mag[1:] == pytest.approx(0, abs=1e-12)


def test_pico_ignora_o_bin_dc():
    mag = np.array([5.0, 0.1, 0.3, 0.2])
    pico = find_peak(mag, np.array([0.0, 10.0, 20.0, 30.0]))
    assert pico == {"bin": 2, "frequency_hz": 20.0, "magnitude": 0.3}