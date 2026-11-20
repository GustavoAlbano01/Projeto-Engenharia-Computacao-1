"""Validação com sinais de referência (T32 - RF010, NF012).

Para cada tom puro de frequência conhecida, em cada taxa de amostragem,
janela e tamanho de bloco, mede a frequência de pico detectada pelo
sistema e o erro em relação à frequência real. O caminho é o mesmo da API:

    gerar_sinais (T10) -> WAV -> read_wav (T11) -> analyze (T20)

Critério (NF012): erro de no máximo um bin, ou seja, |erro| <= fs / N.

Uso (na raiz do repositório, com a .venv ativa):
    python backend/tools/validar_picos.py

Os resultados vão para docs/resultados/:
    validacao_picos.csv  todas as combinações (tons x taxas x janelas x N)
    tabela1_artigo.csv   Tabela 1 do artigo (fs = 44,1 kHz)
"""
import argparse
import csv
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.contract import BLOCK_SIZES, WINDOWS  # noqa: E402
from app.dsp.analysis import analyze           # noqa: E402
from app.dsp.wav_reader import read_wav        # noqa: E402
from tools.gerar_sinais import (TAXAS_PADRAO, gerar_amostras,  # noqa: E402
                                salvar_wav)

FREQUENCIAS_HZ = (440.0, 1000.0)
AMPLITUDE = 0.5
DURACAO_S = 3.0
TAXA_ARTIGO_HZ = 44100
PASTA_SAIDA = BACKEND.parent / "docs" / "resultados"


def validar(freqs=FREQUENCIAS_HZ, taxas=TAXAS_PADRAO, janelas=WINDOWS,
            blocos=BLOCK_SIZES, duracao_s=DURACAO_S):
    """Devolve uma linha (dict) por combinação de tom, taxa, janela e N."""
    linhas = []
    with tempfile.TemporaryDirectory() as pasta:
        for taxa in taxas:
            for freq in freqs:
                # Gera o WAV e lê de volta, como faz o upload.
                caminho = Path(pasta) / f"tom_{freq:g}hz_{taxa}.wav"
                x = gerar_amostras((freq,), (AMPLITUDE,), taxa, duracao_s)
                salvar_wav(caminho, x, taxa)
                audio = read_wav(str(caminho))

                for janela in janelas:
                    for bloco in blocos:
                        r = analyze(audio.samples, audio.sample_rate_hz,
                                    bloco, janela)
                        linhas.append(linha_de_resultado(freq, taxa, r))
    return linhas


def linha_de_resultado(freq, taxa, r):
    detectada = r["peak"]["frequency_hz"]
    erro = detectada - freq
    resolucao = taxa / r["params"]["block_size"]          # Δf = fs / N
    return {
        "frequencia_real_hz": freq,
        "taxa_hz": taxa,
        "janela": r["params"]["window"],
        "n": r["params"]["block_size"],
        "resolucao_hz": round(resolucao, 2),
        "frequencia_detectada_hz": round(detectada, 2),
        "erro_hz": round(erro, 2),
        "erro_relativo_pct": round(abs(erro) / freq * 100, 2),
        "erro_em_bins": round(abs(erro) / resolucao, 3),
        "magnitude_pico": round(r["peak"]["magnitude"], 4),
        "dentro_de_um_bin": abs(erro) <= resolucao,
    }


def tabela_artigo(linhas, taxa=TAXA_ARTIGO_HZ):
    """Colunas da Tabela 1 do artigo, só para uma taxa de amostragem."""
    return [{
        "frequencia_real_hz": linha["frequencia_real_hz"],
        "janela": linha["janela"],
        "n": linha["n"],
        "frequencia_detectada_hz": linha["frequencia_detectada_hz"],
        "erro_hz": linha["erro_hz"],
        "erro_relativo_pct": linha["erro_relativo_pct"],
    } for linha in linhas if linha["taxa_hz"] == taxa]


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
        print("  ".join(f"{str(linha[c]):>12}" for c in colunas))


def resumo(linhas):
    """Totais para a Discussão do artigo."""
    pior = max(linhas, key=lambda linha: linha["erro_em_bins"])
    return {
        "casos": len(linhas),
        "dentro_de_um_bin": sum(linha["dentro_de_um_bin"] for linha in linhas),
        "maior_erro_relativo_pct": max(linha["erro_relativo_pct"]
                                       for linha in linhas),
        "pior_caso": pior,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Valida o pico detectado com tons conhecidos.")
    parser.add_argument("--saida", type=Path, default=PASTA_SAIDA,
                        help="pasta dos CSVs (padrão: docs/resultados/)")
    args = parser.parse_args(argv)

    linhas = validar()
    artigo = tabela_artigo(linhas)

    print(f"Tabela 1 - tons puros, fs = {TAXA_ARTIGO_HZ} Hz")
    imprimir_tabela(artigo)

    salvar_csv(args.saida / "validacao_picos.csv", linhas)
    salvar_csv(args.saida / "tabela1_artigo.csv", artigo)
    print(f"\nResultados salvos em {args.saida.resolve()}")

    r = resumo(linhas)
    pior = r["pior_caso"]
    print(f"\n{r['dentro_de_um_bin']} de {r['casos']} casos com erro de até "
          f"um bin (fs/N). Maior erro relativo: "
          f"{r['maior_erro_relativo_pct']} %.")
    print(f"Pior caso: {pior['frequencia_real_hz']:g} Hz, fs = "
          f"{pior['taxa_hz']} Hz, {pior['janela']}, N = {pior['n']}: "
          f"erro de {pior['erro_hz']} Hz ({pior['erro_em_bins']} bin).")
    return 0 if r["dentro_de_um_bin"] == r["casos"] else 1


if __name__ == "__main__":
    raise SystemExit(main())