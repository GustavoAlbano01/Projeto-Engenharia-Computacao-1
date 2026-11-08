"""DFT direta, de custo O(N²) (T15, RF003).

Calcula a definição da Transformada Discreta de Fourier

    X[k] = Σ x[n] · e^(-2πi·k·n/N),   k, n = 0, 1, ..., N - 1

sem nenhum atalho. Serve só como referência: para conferir a FFT própria
e para o benchmark de tempo DFT × FFT do artigo. O sistema usa a FFT.
"""
import numpy as np


def dft(x):
    """DFT de um vetor x de N amostras. Devolve N valores complexos."""
    x = np.asarray(x, dtype=complex)
    if x.ndim != 1:
        raise ValueError("A DFT direta recebe um vetor (uma dimensão).")
    n_total = len(x)
    if n_total == 0:
        raise ValueError("O vetor de entrada está vazio.")

    n = np.arange(n_total)
    result = np.empty(n_total, dtype=complex)
    for k in range(n_total):          # N frequências ...
        basis = np.exp(-2j * np.pi * k * n / n_total)
        result[k] = np.sum(x * basis)   # ... cada uma soma N termos
    return result