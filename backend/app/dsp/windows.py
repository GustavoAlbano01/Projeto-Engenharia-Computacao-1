"""Funções de janelamento (T14, RF002, RF003).

Implementa as janelas retangular, Hanning e Hamming na forma simétrica,
para n = 0, 1, ..., N - 1:

    Hanning:  w[n] = 0,5  - 0,5  · cos(2πn / (N - 1))
    Hamming:  w[n] = 0,54 - 0,46 · cos(2πn / (N - 1))

Os nomes aceitos são os do contrato da API (app/contract.py).
"""
import numpy as np

from ..contract import WINDOWS


def _cosine_window(a0, a1, n):
    """Janela da forma a0 - a1 · cos(2πn / (N - 1))."""
    i = np.arange(n)
    return a0 - a1 * np.cos(2 * np.pi * i / (n - 1))


def make_window(name, n):
    """Devolve os N coeficientes da janela 'name' como vetor float64."""
    if name not in WINDOWS:
        raise ValueError(f"Janela desconhecida: {name!r}. Use {WINDOWS}.")
    if n < 2:
        raise ValueError("A janela precisa de pelo menos 2 amostras.")

    if name == "rectangular":
        return np.ones(n)
    if name == "hanning":
        return _cosine_window(0.5, 0.5, n)
    return _cosine_window(0.54, 0.46, n)  # hamming


def apply_window(block, name):
    """Multiplica um bloco de amostras pela janela de mesmo tamanho."""
    block = np.asarray(block, dtype=float)
    return block * make_window(name, block.shape[-1])