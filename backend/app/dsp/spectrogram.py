import io

import matplotlib
matplotlib.use("Agg")      # sem janela: só gera arquivos (servidor web)
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
import numpy as np                     # noqa: E402

from .fft import fft                   # noqa: E402
from .spectrum import magnitude        # noqa: E402
from .windows import make_window       # noqa: E402

PISO_DB = -120.0      # mesmo piso do gráfico em dB da INT02
MAX_COLUNAS = 1000    # colunas (blocos) além disso não cabem na imagem
MAX_LINHAS = 256      # menos linhas que a altura do gráfico (~310 px)
BLOCOS_POR_LOTE = 256 # FFTs calculadas de cada vez (limita a memória)

def numero_br(valor, _posicao=None):
    """Número no padrão brasileiro (NF001): 20000 -> "20.000"; 0.5 -> "0,5"."""
    texto = f"{valor:,.3f}".rstrip("0").rstrip(".")      # "20,000" / "0.5"
    return texto.translate(str.maketrans(",.", ".,"))     # troca , e .

def spectrogram_db(samples, sample_rate_hz, block_size, window):
    """Devolve (tempos_s, freqs_hz, db), com db no formato blocos x (N/2+1)."""
    samples = np.asarray(samples, dtype=float)

    # Blocos sucessivos: o bloco k vai da amostra k*N até (k+1)*N - 1.
    # Áudio longo: no máximo MAX_COLUNAS blocos, igualmente espaçados.
    total = len(samples) // block_size
    num_blocos = min(total, MAX_COLUNAS)
    indices = np.round(np.linspace(0, total - 1, num_blocos)).astype(int)
    inicios = indices * block_size

    w = make_window(window, block_size)
    colunas = np.empty((num_blocos, block_size // 2 + 1), dtype=np.float32)
    for a in range(0, num_blocos, BLOCOS_POR_LOTE):
        b = min(a + BLOCOS_POR_LOTE, num_blocos)
        blocos = samples[inicios[a:b, None] + np.arange(block_size)]
        colunas[a:b] = magnitude(fft(blocos * w), w)

    db = np.maximum(20 * np.log10(np.maximum(colunas, 1e-6)), PISO_DB)
    tempos = (inicios + block_size / 2) / sample_rate_hz   # centro do bloco
    freqs = np.arange(block_size // 2 + 1) * sample_rate_hz / block_size
    return tempos, freqs, db


def spectrogram_png(samples, sample_rate_hz, block_size, window, titulo=""):
    """Imagem PNG (bytes) do espectrograma."""
    samples = np.asarray(samples, dtype=float)
    tempos, freqs, db = spectrogram_db(samples, sample_rate_hz,
                                       block_size, window)

    # Mais linhas do que pixels: agrupa faixas vizinhas pelo MÁXIMO, para
    # um tom que ocupa uma faixa só não sumir ao reduzir a imagem.
    fator = -(-db.shape[1] // MAX_LINHAS)      # divisão arredondada para cima
    if fator > 1:
        db = np.maximum.reduceat(db, np.arange(0, db.shape[1], fator), axis=1)

    fig = Figure(figsize=(10, 4.5), dpi=100)
    ax = fig.add_subplot()
    duracao = len(samples) / sample_rate_hz
    img = ax.imshow(db.T, origin="lower", aspect="auto", cmap="magma",
                    interpolation="nearest",
                    extent=[0, duracao, 0, freqs[-1]],
                    vmin=max(PISO_DB, db.max() - 100), vmax=db.max())
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("Frequência (Hz)")
    ax.set_title(titulo)
    barra = fig.colorbar(img, ax=ax, label="Magnitude (dB)")
    formato = FuncFormatter(numero_br)
    for eixo in (ax.xaxis, ax.yaxis, barra.ax.yaxis):
        eixo.set_major_formatter(formato)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    return buffer.getvalue()