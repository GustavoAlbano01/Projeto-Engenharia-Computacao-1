"""Experimento de vazamento espectral (T33 - RF003, RF010).

Compara as janelas retangular, Hanning e Hamming com dois tons puros
(amplitude 0,5, fs = 44,1 kHz, N = 1024, Δf ≈ 43,07 Hz):

- no centro do bin 10 (f = 10 · Δf ≈ 430,66 Hz): referência, sem vazamento;
- entre os bins 10 e 11 (f = 10,5 · Δf ≈ 452,20 Hz): pior caso de vazamento.

O caminho é o mesmo da API: gerar_sinais -> WAV -> read_wav -> analyze.

Uso (na raiz do repositório, com a .venv ativa):
    python backend/tools/experimento_vazamento.py

Os resultados vão para docs/resultados/:
    vazamento.csv             métricas por tom e janela
    figura1_vazamento.png     Figura 1 do artigo
"""
import argparse
import csv
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                 # só gera arquivos, sem abrir janela
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
import numpy as np                    # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.contract import WINDOWS                # noqa: E402
from app.dsp.analysis import analyze            # noqa: E402
from app.dsp.spectrogram import numero_br       # noqa: E402
from app.dsp.wav_reader import read_wav         # noqa: E402
from tools.gerar_sinais import gerar_amostras, salvar_wav  # noqa: E402

FS = 44100
N = 1024
DF = FS / N                    # resolução: ≈ 43,07 Hz
AMPLITUDE = 0.5
DURACAO_S = 3.0
BIN_BASE = 10
TONS = {
    "centro do bin": BIN_BASE * DF,           # ≈ 430,66 Hz
    "entre dois bins": (BIN_BASE + 0.5) * DF,  # ≈ 452,20 Hz
}
PISO_DB = -120.0
PASTA_SAIDA = BACKEND.parent / "docs" / "resultados"

NOMES = {"rectangular": "Retangular", "hanning": "Hanning",
         "hamming": "Hamming"}
# Cores com contraste e diferença de claridade; o tipo de linha também
# distingue as janelas (a figura continua legível impressa em preto e branco).
ESTILO = {
    "rectangular": {"color": "#2E9E8F", "linestyle": "-"},
    "hamming": {"color": "#2F6FB0", "linestyle": "--"},
    "hanning": {"color": "#C2611F", "linestyle": ":"},
}


def espectro(freq, janela, pasta, duracao_s=DURACAO_S):
    """Analisa um tom puro com o mesmo caminho do upload + análise."""
    caminho = Path(pasta) / f"tom_{freq:.2f}hz.wav"
    if not caminho.exists():
        x = gerar_amostras((freq,), (AMPLITUDE,), FS, duracao_s)
        salvar_wav(caminho, x, FS)
    audio = read_wav(str(caminho))
    return analyze(audio.samples, audio.sample_rate_hz, N, janela)


def em_db(magnitudes):
    m = np.maximum(np.asarray(magnitudes, dtype=float), 1e-6)
    return np.maximum(20 * np.log10(m), PISO_DB)


def metricas(tom, freq, janela, r):
    """Números que resumem o vazamento de uma janela."""
    mags = np.asarray(r["magnitudes"])
    k = r["peak"]["bin"]
    pico = mags[k]
    relativo_db = em_db(mags) - em_db([pico])[0]   # 0 dB no pico
    perda_db = float(20 * np.log10(pico / AMPLITUDE))
    return {
        "tom": tom,
        "frequencia_hz": round(freq, 2),
        "janela": janela,
        "frequencia_detectada_hz": round(r["peak"]["frequency_hz"], 2),
        "magnitude_pico": round(float(pico), 4),
        "perda_amplitude_db": round(perda_db, 2) + 0.0,
        # nível a 10 e a 30 bins do pico, em relação ao pico
        "nivel_10_bins_db": round(float(relativo_db[k + 10]), 1),
        "nivel_30_bins_db": round(float(relativo_db[k + 30]), 1),
        # quantos bins ficam a menos de 40 dB do pico (espalhamento)
        "bins_acima_de_menos_40db": int(np.sum(relativo_db >= -40)),
    }


def rodar(duracao_s=DURACAO_S):
    """Devolve (linhas de métricas, espectros do tom entre dois bins)."""
    linhas = []
    espectros = {}
    with tempfile.TemporaryDirectory() as pasta:
        for tom, freq in TONS.items():
            for janela in WINDOWS:
                r = espectro(freq, janela, pasta, duracao_s)
                linhas.append(metricas(tom, freq, janela, r))
                if tom == "entre dois bins":
                    espectros[janela] = r
    return linhas, espectros


# ---------- Figura 1 ----------
def figura(espectros, caminho):
    """(a) espectro em dB de 0 a 2 kHz; (b) detalhe linear perto do pico."""
    freq = TONS["entre dois bins"]
    fig = Figure(figsize=(7.5, 3.2), dpi=300)
    ax_db, ax_lin = fig.subplots(1, 2, gridspec_kw={"width_ratios": [1.4, 1]})

    for janela in ("rectangular", "hamming", "hanning"):
        r = espectros[janela]
        f = np.asarray(r["frequencies_hz"])
        m = np.asarray(r["magnitudes"])
        estilo = dict(ESTILO[janela], linewidth=1.2, label=NOMES[janela])
        ax_db.plot(f, em_db(m), **estilo)
        perto = (f >= freq - 8 * DF) & (f <= freq + 8 * DF)
        ax_lin.plot(f[perto], m[perto], marker="o", markersize=3, **estilo)

    ax_db.set_xlim(0, 2000)
    ax_db.set_ylim(PISO_DB, 0)
    ax_db.set_xlabel("Frequência (Hz)")
    ax_db.set_ylabel("Magnitude (dB)")
    ax_db.set_title("(a) Espectro em dB", fontsize=9)

    ax_lin.axhline(AMPLITUDE, color="#6b6b6b", linewidth=0.8,
                   linestyle="-.", label="Amplitude real")
    ax_lin.set_xlim(freq - 8 * DF, freq + 8 * DF)
    ax_lin.set_ylim(0, 0.55)
    ax_lin.set_xlabel("Frequência (Hz)")
    ax_lin.set_ylabel("Magnitude")
    ax_lin.set_title("(b) Detalhe perto do pico", fontsize=9)

    for ax in (ax_db, ax_lin):
        ax.axvline(freq, color="#6b6b6b", linewidth=0.8, linestyle=(0, (1, 2)))
        ax.grid(True, color="#e3e3e3", linewidth=0.5)
        ax.tick_params(labelsize=7)
        ax.xaxis.label.set_size(8)
        ax.yaxis.label.set_size(8)
        ax.xaxis.set_major_formatter(FuncFormatter(numero_br))
        ax.yaxis.set_major_formatter(FuncFormatter(numero_br))
    ax_lin.legend(fontsize=7, loc="upper right")

    fig.tight_layout()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(caminho)


# ---------- saída ----------
def salvar_csv(caminho, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


def imprimir_tabela(linhas):
    colunas = list(linhas[0])
    print("  ".join(f"{c[:12]:>12}" for c in colunas))
    for linha in linhas:
        print("  ".join(f"{str(linha[c])[:12]:>12}" for c in colunas))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Experimento de vazamento espectral.")
    parser.add_argument("--saida", type=Path, default=PASTA_SAIDA,
                        help="pasta dos resultados (padrão: docs/resultados/)")
    args = parser.parse_args(argv)

    linhas, espectros = rodar()
    imprimir_tabela(linhas)

    salvar_csv(args.saida / "vazamento.csv", linhas)
    figura(espectros, args.saida / "figura1_vazamento.png")
    print(f"\nResultados salvos em {args.saida.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())