"""Gerador de sinais de teste (T10, RF010).

Cria arquivos WAV PCM 16 bits, mono, com frequência conhecida, para validar
a análise espectral: tons puros de 440 Hz e 1 kHz e a soma dos dois tons,
em várias taxas de amostragem. Também grava sinais.csv com os parâmetros
de cada arquivo, para conferir o pico detectado.

Uso (na raiz do repositório):
    python backend/tools/gerar_sinais.py
    python backend/tools/gerar_sinais.py --taxas 44100 48000 --duracao 5
"""
import argparse
import csv
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

TAXAS_PADRAO = (8000, 22050, 44100, 48000)
DURACAO_PADRAO_S = 3.0
PASTA_PADRAO = Path(__file__).resolve().parents[2] / "sinais_teste"

AMPLITUDE_TOM = 0.5         # um tom puro: pico esperado perto de 0,5
AMPLITUDE_DOIS_TONS = 0.4   # cada tom; a soma fica abaixo de 1 (sem saturar)
MAX_INT16 = 32767


@dataclass(frozen=True)
class Sinal:
    """Um sinal a gerar: soma de senoides com frequências e amplitudes."""
    nome: str
    frequencias_hz: tuple
    amplitudes: tuple


SINAIS = (
    Sinal("tom_440hz", (440.0,), (AMPLITUDE_TOM,)),
    Sinal("tom_1000hz", (1000.0,), (AMPLITUDE_TOM,)),
    Sinal("dois_tons_440_1000hz", (440.0, 1000.0),
          (AMPLITUDE_DOIS_TONS, AMPLITUDE_DOIS_TONS)),
)


def gerar_amostras(frequencias_hz, amplitudes, taxa_hz, duracao_s):
    """Soma de senoides, em ponto flutuante, com valores entre -1 e 1."""
    for f in frequencias_hz:
        if not 0 < f < taxa_hz / 2:
            raise ValueError(
                f"{f} Hz fora do intervalo (0, {taxa_hz / 2}) Hz: "
                "a frequência deve ficar abaixo de Nyquist (fs/2)")
    if sum(amplitudes) > 1:
        raise ValueError("soma das amplitudes acima de 1 saturaria o sinal")

    n = np.arange(round(taxa_hz * duracao_s))
    t = n / taxa_hz
    x = np.zeros(len(n))
    for f, a in zip(frequencias_hz, amplitudes):
        x += a * np.sin(2 * np.pi * f * t)
    return x


def salvar_wav(caminho, amostras, taxa_hz):
    """Grava as amostras (-1 a 1) como WAV PCM 16 bits mono."""
    pcm = np.round(np.clip(amostras, -1, 1) * MAX_INT16).astype("<i2")
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa_hz)
        w.writeframes(pcm.tobytes())


def gerar_todos(pasta=PASTA_PADRAO, taxas=TAXAS_PADRAO,
                duracao_s=DURACAO_PADRAO_S):
    """Gera todos os sinais em todas as taxas. Devolve os caminhos criados."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    criados = []
    linhas = []
    for taxa in taxas:
        for s in SINAIS:
            caminho = pasta / f"{s.nome}_{taxa}.wav"
            x = gerar_amostras(s.frequencias_hz, s.amplitudes,
                               taxa, duracao_s)
            salvar_wav(caminho, x, taxa)
            criados.append(caminho)
            linhas.append({
                "arquivo": caminho.name,
                "taxa_hz": taxa,
                "duracao_s": duracao_s,
                "frequencias_hz": " + ".join(
                    f"{f:g}" for f in s.frequencias_hz),
                "amplitudes": " + ".join(f"{a:g}" for a in s.amplitudes),
            })

    with open(pasta / "sinais.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    return criados


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Gerador de sinais de teste (T10, RF010).")
    parser.add_argument("--saida", type=Path, default=PASTA_PADRAO,
                        help="pasta de saída (padrão: sinais_teste/ na raiz)")
    parser.add_argument("--taxas", type=int, nargs="+", default=TAXAS_PADRAO,
                        help="taxas de amostragem em Hz")
    parser.add_argument("--duracao", type=float, default=DURACAO_PADRAO_S,
                        help="duração de cada sinal em segundos")
    args = parser.parse_args(argv)

    criados = gerar_todos(args.saida, args.taxas, args.duracao)
    print(f"{len(criados)} arquivos gerados em {args.saida.resolve()}")


if __name__ == "__main__":
    main()