"""Testes da DFT direta (T15).

O numpy.fft é usado só como referência.
"""
import numpy as np
import pytest

from app.dsp.dft import dft


@pytest.mark.parametrize("n", (8, 100, 512))
def test_igual_ao_numpy(n):
    x = np.random.default_rng(n).standard_normal(n)
    assert dft(x) == pytest.approx(np.fft.fft(x), abs=1e-8)


def test_impulso_tem_espectro_plano():
    x = np.zeros(16)
    x[0] = 1
    assert dft(x) == pytest.approx(np.ones(16))


def test_cosseno_concentra_energia_no_seu_bin():
    n, k = 64, 5
    x = np.cos(2 * np.pi * k * np.arange(n) / n)
    mag = np.abs(dft(x))
    assert mag[k] == pytest.approx(n / 2)
    assert mag[n - k] == pytest.approx(n / 2)   # espelho do bin k
    mag[[k, n - k]] = 0
    assert mag.max() == pytest.approx(0, abs=1e-9)


def test_recusa_vetor_vazio():
    with pytest.raises(ValueError):
        dft([])