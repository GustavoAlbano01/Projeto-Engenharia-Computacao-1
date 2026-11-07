"""Magnitude, eixo de frequência e pico (T17, RF003).

Convenções do contrato da API (docs/CONTRATO_API.md):

- só as componentes k = 0 ... N/2 (até a frequência de Nyquist);
- frequência de k: f = k · fs / N; resolução Δf = fs / N;
- magnitude normalizada: |X[k]| / Σ w[n], multiplicada por 2 exceto em
  k = 0 e k = N/2, para que uma senoide de amplitude A dê pico perto de A;
- pico: maior magnitude ignorando o bin 0 (componente DC).
"""
import numpy as np


def frequencies(block_size, sample_rate_hz):
    """Frequência, em Hz, de cada bin k = 0 ... N/2."""
    k = np.arange(block_size // 2 + 1)
    return k * sample_rate_hz / block_size


def freq_resolution(block_size, sample_rate_hz):
    """Largura de um bin, em Hz (Δf = fs / N)."""
    return sample_rate_hz / block_size


def magnitude(spectrum, window):
    """Magnitude normalizada dos bins 0 ... N/2.

    'spectrum' é a saída da FFT de um bloco já janelado (ou de vários
    blocos, um por linha); 'window' são os coeficientes da janela usada.
    """
    spectrum = np.asarray(spectrum)
    n = spectrum.shape[-1]
    mag = np.abs(spectrum[..., :n // 2 + 1]) / np.sum(window)
    mag[..., 1:n // 2] *= 2   # bins 0 e N/2 não dobram
    return mag


def find_peak(magnitudes, freqs):
    """Pico do espectro, ignorando o bin 0 (DC), no formato do contrato."""
    magnitudes = np.asarray(magnitudes)
    if len(magnitudes) < 2:
        raise ValueError("O espectro precisa de pelo menos 2 bins.")
    k = int(np.argmax(magnitudes[1:])) + 1
    return {
        "bin": k,
        "frequency_hz": float(freqs[k]),
        "magnitude": float(magnitudes[k]),
    }