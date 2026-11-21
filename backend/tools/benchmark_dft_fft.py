"""Benchmark DFT direta x FFT própria (T34 - RF003).

Mede o tempo de um bloco com a DFT direta (T15) e com a FFT radix-2 (T16)
para N = 64 até 8192 (DFT) e até 65536 (FFT), e confirma a ordem de
crescimento de cada uma pela inclinação da reta em escala log-log:

    t ∝ N^a  ->  log t = a · log N + b

DFT: espera-se a ≈ 2 (custo N²). FFT: espera-se a ≈ 1, um pouco acima,
por causa do fator log N (custo N·log2 N).

A inclinação é calculada só com os N grandes: com N pequeno o tempo é
dominado pelo custo fixo das chamadas do Python, não pela conta em si.

Uso (na raiz do repositório, com a .venv ativa):
    python backend/tools/benchmark_dft_fft.py

Os resultados vão para docs/resultados/:
    benchmark_dft_fft.csv    tempos por N
    benchmark_dft_fft.md     ambiente da medição e inclinações
    figura2_dft_fft.png      Figura 2 do artigo (escala log-log)
"""
import argparse
import csv
import math
import platform
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                 # só gera arquivos, sem abrir janela
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
import numpy as np                    # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.dsp.dft import dft    # noqa: E402
from app.dsp.fft import fft    # noqa: E402

N_DFT = [2 ** k for k in range(6, 14)]     # 64 ... 8192
N_FFT = [2 ** k for k in range(6, 17)]     # 64 ... 65536
N_MIN_DFT_AJUSTE = 1024     # inclinação calculada a partir destes N
N_MIN_FFT_AJUSTE = 2048
REPETICOES = 5              # o menor tempo de 5 medições
TEMPO_MIN_MEDICAO_S = 0.01  # chamadas rápidas são repetidas em laço
PASTA_SAIDA = BACKEND.parent / "docs" / "resultados"

COR_DFT = "#C2611F"
COR_FFT = "#2F6FB0"
COR_REF = "#6b6b6b"

# ---------- medição ----------
def cronometrar(funcao, x, repeticoes=REPETICOES):
    """Menor tempo (s) de uma chamada, em 'repeticoes' medições.

    Chamadas muito rápidas são repetidas em laço dentro de cada medição,
    para o tempo medido ficar bem acima da resolução do relógio.
    """
    inicio = time.perf_counter()
    funcao(x)                                   # aquece e estima o tempo
    estimativa = time.perf_counter() - inicio
    laco = max(1, math.ceil(TEMPO_MIN_MEDICAO_S / max(estimativa, 1e-9)))

    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        for _ in range(laco):
            funcao(x)
        tempos.append((time.perf_counter() - inicio) / laco)
    return min(tempos)    # o menor é o que sofreu menos interferência

def medir(ns_dft=N_DFT, ns_fft=N_FFT, repeticoes=REPETICOES):
    """Uma linha por N. A DFT fica vazia acima do maior N de ns_dft."""
    rng = np.random.default_rng(0)        # semente fixa: mesmo sinal sempre
    linhas = []
    for n in sorted(set(ns_dft) | set(ns_fft)):
        x = rng.uniform(-1, 1, n)
        t_fft = cronometrar(fft, x, repeticoes) if n in ns_fft else None
        t_dft = None
        if n in ns_dft:
            # A DFT lenta também confere a FFT: as duas devem coincidir.
            if not np.allclose(fft(x), dft(x), atol=1e-6):
                raise RuntimeError(f"FFT e DFT diferentes para N = {n}")
            t_dft = cronometrar(dft, x, repeticoes)
        linhas.append({
            "n": n,
            "dft_ms": None if t_dft is None else round(t_dft * 1000, 4),
            "fft_ms": None if t_fft is None else round(t_fft * 1000, 4),
            "razao_medida": (None if t_dft is None or t_fft is None
                             else round(t_dft / t_fft, 1)),
            "razao_teorica": round(n / math.log2(n), 1),   # N² / (N·log N)
        })
    return linhas

# ---------- ordem de crescimento ----------
def inclinacao(ns, tempos):
    """Expoente 'a' de t ∝ N^a, pela reta de mínimos quadrados em log-log."""
    a, _b = np.polyfit(np.log2(ns), np.log2(tempos), 1)
    return float(a)

def inclinacoes(linhas):
    dft_pts = [(r["n"], r["dft_ms"]) for r in linhas
               if r["dft_ms"] is not None and r["n"] >= N_MIN_DFT_AJUSTE]
    fft_pts = [(r["n"], r["fft_ms"]) for r in linhas
               if r["fft_ms"] is not None and r["n"] >= N_MIN_FFT_AJUSTE]
    # Referência teórica da FFT nos mesmos N: inclinação de N·log2 N.
    n_fft = [n for n, _ in fft_pts]
    teorica_fft = inclinacao(n_fft, [n * math.log2(n) for n in n_fft])
    return {
        "dft": inclinacao(*zip(*dft_pts)),
        "fft": inclinacao(*zip(*fft_pts)),
        "fft_teorica": teorica_fft,
        "n_dft": (dft_pts[0][0], dft_pts[-1][0]),
        "n_fft": (fft_pts[0][0], fft_pts[-1][0]),
    }

# ---------- Figura 2 ----------
def numero_curto(valor, _posicao=None):
    """0.01 -> "0,01"; 1000 -> "1000" (eixos em escala log)."""
    return f"{valor:g}".replace(".", ",")

def figura(linhas, caminho):
    dft_pts = [(r["n"], r["dft_ms"]) for r in linhas if r["dft_ms"]]
    fft_pts = [(r["n"], r["fft_ms"]) for r in linhas if r["fft_ms"]]

    fig = Figure(figsize=(6.0, 3.8), dpi=300)
    ax = fig.add_subplot()
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")

    ax.plot(*zip(*dft_pts), color=COR_DFT, marker="o", markersize=4,
            linewidth=1.4, label="DFT direta")
    ax.plot(*zip(*fft_pts), color=COR_FFT, marker="s", markersize=4,
            linewidth=1.4, label="FFT radix-2 própria")

    # Curvas teóricas, ancoradas no maior N medido de cada algoritmo.
    # Só na faixa usada no ajuste (N grandes), como na inclinação.
    n_d, t_d = dft_pts[-1]
    ns = np.array([n for n, _ in dft_pts if n >= N_MIN_DFT_AJUSTE],
                  dtype=float)
    ax.plot(ns, t_d * (ns / n_d) ** 2, color=COR_REF, linestyle="--",
            linewidth=0.9, label="∝ N² (teórico)")
    n_f, t_f = fft_pts[-1]
    ns = np.array([n for n, _ in fft_pts if n >= N_MIN_FFT_AJUSTE],
                  dtype=float)
    ax.plot(ns, t_f * (ns * np.log2(ns)) / (n_f * math.log2(n_f)),
            color=COR_REF, linestyle=":", linewidth=1.2,
            label="∝ N·log₂N (teórico)")

    ax.set_xlabel("Tamanho do bloco N (amostras)", fontsize=8)
    ax.set_ylabel("Tempo de um bloco (ms)", fontsize=8)
    ax.set_xticks([r["n"] for r in linhas])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: f"{v:.0f}"))
    ax.yaxis.set_major_formatter(FuncFormatter(numero_curto))
    ax.tick_params(labelsize=7)
    ax.tick_params(axis="x", labelrotation=45)
    ax.grid(True, which="major", color="#e3e3e3", linewidth=0.5)
    ax.legend(fontsize=7, loc="upper left")

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

def br(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")

def resumo_md(linhas, inc):
    """Texto em Markdown com o ambiente e as conclusões numéricas."""
    maior = max((r for r in linhas if r["razao_medida"]),
                key=lambda r: r["n"])
    return "\n".join([
        "# Benchmark DFT × FFT (T34) - valores medidos",
        "",
        "Gerado por `python backend/tools/benchmark_dft_fft.py`.",
        "",
        "## Ambiente",
        f"- Data: {time.strftime('%d/%m/%Y')}",
        f"- Processador: {platform.processor() or platform.machine()}",
        f"- Sistema: {platform.system()} {platform.release()}",
        f"- Python {platform.python_version()}, NumPy {np.__version__}",
        "",
        "## Ordem de crescimento (inclinação em log-log, t ∝ N^a)",
        f"- DFT direta: a = {br(inc['dft'])} (teórico: 2), "
        f"N de {inc['n_dft'][0]} a {inc['n_dft'][1]}.",
        f"- FFT própria: a = {br(inc['fft'])} (teórico para N·log₂N "
        f"nesses N: {br(inc['fft_teorica'])}), "
        f"N de {inc['n_fft'][0]} a {inc['n_fft'][1]}.",
        "",
        "## Ganho da FFT",
        f"- Com N = {maior['n']}: DFT {br(maior['dft_ms'], 1)} ms, FFT "
        f"{br(maior['fft_ms'], 3)} ms, FFT {br(maior['razao_medida'], 0)} "
        f"vezes mais rápida (razão teórica N/log₂N = "
        f"{br(maior['razao_teorica'], 0)}).",
        "",
    ])

def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark DFT x FFT.")
    parser.add_argument("--saida", type=Path, default=PASTA_SAIDA,
                        help="pasta dos resultados (padrão: docs/resultados/)")
    parser.add_argument("--n-max-dft", type=int, default=N_DFT[-1],
                        help="maior N da DFT (a DFT de 8192 leva ~2 s)")
    parser.add_argument("--n-max-fft", type=int, default=N_FFT[-1],
                        help="maior N da FFT")
    parser.add_argument("--repeticoes", type=int, default=REPETICOES)
    args = parser.parse_args(argv)

    ns_dft = [n for n in N_DFT if n <= args.n_max_dft]
    ns_fft = [n for n in N_FFT if n <= args.n_max_fft]
    print("Medindo (a DFT com N = 8192 leva alguns segundos)...\n")
    linhas = medir(ns_dft, ns_fft, args.repeticoes)

    print(f"{'N':>6}  {'DFT (ms)':>10}  {'FFT (ms)':>10}  "
          f"{'razão':>8}  {'teórica':>8}")
    for r in linhas:
        print(f"{r['n']:>6}  {str(r['dft_ms'] or '-'):>10}  "
              f"{str(r['fft_ms']):>10}  {str(r['razao_medida'] or '-'):>8}  "
              f"{r['razao_teorica']:>8}")

    inc = inclinacoes(linhas)
    texto = resumo_md(linhas, inc)
    salvar_csv(args.saida / "benchmark_dft_fft.csv", linhas)
    (args.saida / "benchmark_dft_fft.md").write_text(texto, encoding="utf-8")
    figura(linhas, args.saida / "figura2_dft_fft.png")

    print(f"\nInclinação DFT: {inc['dft']:.2f} (teórico 2)")
    print(f"Inclinação FFT: {inc['fft']:.2f} "
          f"(teórico N·log2 N: {inc['fft_teorica']:.2f})")
    print(f"Resultados salvos em {args.saida.resolve()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())