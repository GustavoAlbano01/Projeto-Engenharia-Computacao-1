"""FFT radix-2 própria, algoritmo de Cooley e Tukey (T16, RF003).

Versão iterativa, em dois passos:

1. Reordena as amostras pela inversão dos bits do índice
   (ex.: com N = 8, o índice 1 = 001 vai para 4 = 100).
2. Combina pares de DFTs menores com "borboletas", em log2(N) estágios:
   tamanho 2, 4, 8, ..., N. Em cada grupo de tamanho M:

       X[k]       = par[k] + W^k · ímpar[k]
       X[k + M/2] = par[k] - W^k · ímpar[k],   W = e^(-2πi/M)

O custo total é proporcional a N·log2(N). N precisa ser potência de 2.
Aceita um bloco (vetor) ou vários blocos de uma vez (matriz blocos × N),
calculando a FFT de cada linha. Não usa nenhuma função de FFT de biblioteca.
"""
import numpy as np


def is_power_of_two(n):
    return n > 0 and n & (n - 1) == 0


def bit_reverse_indices(n):
    """Índices 0..N-1 com os bits invertidos (N potência de 2)."""
    bits = n.bit_length() - 1
    indices = np.arange(n)
    reversed_idx = np.zeros(n, dtype=int)
    for b in range(bits):
        bit = (indices >> b) & 1
        reversed_idx |= bit << (bits - 1 - b)
    return reversed_idx


def fft(x):
    """FFT de x ao longo do último eixo. Devolve valores complexos."""
    x = np.asarray(x, dtype=complex)
    n = x.shape[-1]
    if not is_power_of_two(n):
        raise ValueError(f"N = {n} não é potência de 2.")

    shape = x.shape
    data = x[..., bit_reverse_indices(n)]

    size = 2
    while size <= n:
        half = size // 2
        w = np.exp(-2j * np.pi * np.arange(half) / size)  # fatores W^k
        groups = data.reshape(*shape[:-1], n // size, size)
        even = groups[..., :half]
        odd = groups[..., half:] * w
        data = np.concatenate([even + odd, even - odd], axis=-1)
        size *= 2

    return data.reshape(shape)