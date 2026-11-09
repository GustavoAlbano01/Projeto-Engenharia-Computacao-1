"""Análise espectral de um áudio (T18, T20 - RF002, RF003).

- choose_block_size: ajusta o bloco maior que o áudio (T18).
- block_starts: até 256 blocos igualmente espaçados, sem sobreposição.
- analyze: janela + FFT própria + média dos blocos + pico.
"""

import numpy as np

from ..contract import BLOCK_SIZES
from .fft import fft
from .spectrum import find_peak, freq_resolution, frequencies, magnitude
from .windows import make_window

MIN_BLOCK_SIZE = min(BLOCK_SIZES)   # 512
MAX_BLOCKS = 256                    # decisão de 20/09 (NF004)

MIN_BLOCK_SIZE = min(BLOCK_SIZES)   # 512


class AudioTooShortError(Exception):
    """Áudio menor que o menor bloco permitido -> erro 400."""
    code = "AUDIO_TOO_SHORT"


def choose_block_size(requested, num_samples):
    """Devolve (bloco_usado, lista_de_avisos)."""
    # 1. Nem o menor bloco cabe: não dá para analisar.
    if num_samples < MIN_BLOCK_SIZE:
        raise AudioTooShortError(
            f"O áudio tem {num_samples} amostras; o mínimo é {MIN_BLOCK_SIZE}.")

    # 2. O bloco pedido cabe: usa sem mudar nada.
    if requested <= num_samples:
        return requested, []

    # 3. Não cabe: procura o maior bloco permitido que cabe.
    #    BLOCK_SIZES está em ordem crescente (512, 1024, 2048, 4096),
    #    então o último que passar no teste é o maior.
    used = MIN_BLOCK_SIZE
    for size in BLOCK_SIZES:
        if size <= num_samples:
            used = size

    warning = {
        "code": "BLOCK_SIZE_ADJUSTED",
        "message": (f"O bloco solicitado ({requested}) é maior que o áudio. "
                    f"Foi usado {used}."),
        "details": {"requested": requested, "used": used},
    }
    return used, [warning]

def block_starts(num_samples, block_size, max_blocks=MAX_BLOCKS):
    """Índices de início de até 'max_blocks' blocos igualmente espaçados.

    B = mín(max_blocks, L // N). Com B <= L // N o espaçamento é >= N,
    então os blocos nunca se sobrepõem.
    """
    num_blocks = min(max_blocks, num_samples // block_size)
    if num_blocks == 1:
        return np.array([0])

    last_start = num_samples - block_size     # último bloco termina em L
    starts = np.linspace(0, last_start, num_blocks)
    return np.round(starts).astype(int)


def analyze(samples, sample_rate_hz, block_size, window):
    """Espectro médio no formato do contrato (sem id, audio e created_at)."""
    samples = np.asarray(samples, dtype=float)

    # 1. Bloco que será usado (pode ser ajustado - T18)
    used, warnings = choose_block_size(block_size, len(samples))

    # 2. Recorta os blocos: matriz B x N
    starts = block_starts(len(samples), used)
    indices = starts[:, None] + np.arange(used)
    blocks = samples[indices]

    # 3. Janela + FFT de cada linha + magnitude normalizada (T14, T16, T17)
    w = make_window(window, used)
    spectra = fft(blocks * w)
    mags = magnitude(spectra, w)          # B x (N/2 + 1)

    # 4. Média dos blocos e pico
    mean_mag = mags.mean(axis=0)          # N/2 + 1 valores
    freqs = frequencies(used, sample_rate_hz)
    peak = find_peak(mean_mag, freqs)

    return {
        "params": {"block_size": used, "window": window},
        "blocks_used": len(starts),
        "freq_resolution_hz": round(freq_resolution(used, sample_rate_hz), 4),
        "frequencies_hz": [round(float(f), 2) for f in freqs],
        "magnitudes": [round(float(m), 6) for m in mean_mag],
        "peak": peak,
        "warnings": warnings,
    }