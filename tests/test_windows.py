"""Testes das funções de janelamento (T14).

As janelas são conferidas com o scipy.signal, usado só como referência.
"""
import numpy as np
import pytest
from scipy.signal import windows as ref

from app.contract import BLOCK_SIZES, WINDOWS
from app.dsp.windows import apply_window, make_window

REFERENCIA = {
    "rectangular": ref.boxcar,
    "hanning": ref.hann,
    "hamming": ref.hamming,
}


@pytest.mark.parametrize("n", BLOCK_SIZES)
@pytest.mark.parametrize("name", WINDOWS)
def test_igual_ao_scipy(name, n):
    esperado = REFERENCIA[name](n, sym=True)
    assert make_window(name, n) == pytest.approx(esperado, abs=1e-12)


@pytest.mark.parametrize("name", WINDOWS)
def test_simetrica(name):
    w = make_window(name, 1024)
    assert w == pytest.approx(w[::-1], abs=1e-12)


def test_valores_nas_pontas_e_no_centro():
    hann = make_window("hanning", 1025)     # N ímpar: tem centro exato
    hamm = make_window("hamming", 1025)
    assert hann[0] == pytest.approx(0) and hann[-1] == pytest.approx(0)
    assert hamm[0] == pytest.approx(0.08) and hamm[-1] == pytest.approx(0.08)
    assert hann[512] == pytest.approx(1) and hamm[512] == pytest.approx(1)


def test_aplicar_janela_multiplica_amostra_a_amostra():
    bloco = np.full(512, 2.0)
    assert apply_window(bloco, "hanning") == pytest.approx(
        2 * make_window("hanning", 512))


def test_recusa_nome_desconhecido():
    with pytest.raises(ValueError):
        make_window("blackman", 512)