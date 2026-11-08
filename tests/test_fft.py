"""Testes da FFT radix-2 própria (T16).

O numpy.fft é usado só como referência.
"""
import numpy as np
import pytest

from app.contract import BLOCK_SIZES
from app.dsp.fft import bit_reverse_indices, fft


def test_inversao_de_bits_com_n_8():
    assert bit_reverse_indices(8).tolist() == [0, 4, 2, 6, 1, 5, 3, 7]


@pytest.mark.parametrize("n", BLOCK_SIZES)
def test_igual_ao_numpy(n):
    x = np.random.default_rng(n).standard_normal(n)
    assert fft(x) == pytest.approx(np.fft.fft(x), abs=1e-8)


def test_varios_blocos_de_uma_vez():
    blocos = np.random.default_rng(2).standard_normal((10, 1024))
    resultado = fft(blocos)
    assert resultado.shape == (10, 1024)
    assert resultado == pytest.approx(np.fft.fft(blocos, axis=-1), abs=1e-8)


@pytest.mark.parametrize("n", (0, 3, 100, 1000))
def test_recusa_tamanho_que_nao_e_potencia_de_2(n):
    with pytest.raises(ValueError):
        fft(np.zeros(n))