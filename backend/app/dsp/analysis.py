"""Escolha do tamanho de bloco da análise (T18, RF002).

Fluxo alternativo do RF002: se o bloco pedido for maior que o áudio,
usa o maior bloco permitido que cabe e avisa o usuário.
"""
from ..contract import BLOCK_SIZES

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