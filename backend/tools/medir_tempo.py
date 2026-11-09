"""Medição do tempo de resposta (T21 - NF004) e benchmark DFT x FFT.

Mede o POST /api/analyses no pior caso aceito pelo sistema (WAV de 5 min,
48 kHz, estéreo, ~57,6 MB) para todos os blocos e janelas, e compara o
tempo da DFT direta (T15) com a FFT própria (T16) em um bloco.

Uso (na raiz do repositório, com a .venv ativa):
    python backend/tools/medir_tempo.py
    python backend/tools/medir_tempo.py --repeticoes 5

Os resultados vão para docs/resultados/ (tempo_resposta.csv e dft_fft.csv).
"""
import argparse
import csv
import io
import statistics
import sys
import tempfile
import time
import wave
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app import create_app                  # noqa: E402
from app.contract import BLOCK_SIZES, WINDOWS  # noqa: E402
from app.dsp.dft import dft                 # noqa: E402
from app.dsp.fft import fft                 # noqa: E402
from tools.gerar_sinais import gerar_amostras  # noqa: E402

LIMITE_S = 2.0                               # NF004
PASTA_SAIDA = BACKEND.parent / "docs" / "resultados"


# ---------- sinal de pior caso ----------
def wav_pior_caso(taxa_hz=48000, duracao_s=300.0):
    """WAV PCM 16 bits estéreo, montado em memória. Devolve os bytes."""
    x = gerar_amostras((440.0, 1000.0), (0.4, 0.4), taxa_hz, duracao_s)
    estereo = np.column_stack([x, x])                 # L = R
    pcm = np.round(estereo * 32767).astype("<i2")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(taxa_hz)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


# ---------- Tabela 1: tempo pela API ----------
def medir_api(dados, repeticoes):
    linhas = []
    with tempfile.TemporaryDirectory() as pasta:
        app = create_app(upload_dir=Path(pasta),
                         db_url="sqlite:///:memory:")
        client = app.test_client()

        inicio = time.perf_counter()
        resp = client.post("/api/audios",
                           data={"file": (io.BytesIO(dados), "pior_caso.wav")},
                           content_type="multipart/form-data")
        tempo_upload = time.perf_counter() - inicio
        if resp.status_code != 201:
            raise RuntimeError(f"Upload falhou: {resp.get_json()}")
        audio_id = resp.get_json()["id"]

        for bloco in BLOCK_SIZES:
            for janela in WINDOWS:
                tempos = []
                for _ in range(repeticoes):
                    inicio = time.perf_counter()
                    r = client.post("/api/analyses", json={
                        "audio_id": audio_id,
                        "block_size": bloco,
                        "window": janela,
                    })
                    tempos.append(time.perf_counter() - inicio)
                    if r.status_code != 201:
                        raise RuntimeError(f"Análise falhou: {r.get_json()}")
                linhas.append({
                    "block_size": bloco,
                    "window": janela,
                    "media_s": round(statistics.mean(tempos), 3),
                    "max_s": round(max(tempos), 3),
                    "atende_nf004": max(tempos) <= LIMITE_S,
                })
    return tempo_upload, linhas


# ---------- Tabela 2: DFT x FFT ----------
def medir_dft_fft(repeticoes_fft=20):
    rng = np.random.default_rng(0)        # semente fixa: resultado reproduzível
    linhas = []
    for n in BLOCK_SIZES:
        x = rng.uniform(-1, 1, n)

        inicio = time.perf_counter()
        dft(x)                             # lenta: 1 execução basta
        t_dft = time.perf_counter() - inicio

        inicio = time.perf_counter()
        for _ in range(repeticoes_fft):    # rápida: média de várias
            fft(x)
        t_fft = (time.perf_counter() - inicio) / repeticoes_fft

        linhas.append({
            "n": n,
            "dft_ms": round(t_dft * 1000, 3),
            "fft_ms": round(t_fft * 1000, 3),
            "razao_medida": round(t_dft / t_fft, 1),
            "razao_teorica": round(n / np.log2(n), 1),
        })
    return linhas


# ---------- saída ----------
def salvar_csv(caminho, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


def imprimir_tabela(linhas):
    colunas = list(linhas[0])
    print("  ".join(f"{c:>14}" for c in colunas))
    for linha in linhas:
        print("  ".join(f"{str(linha[c]):>14}" for c in colunas))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Mede o tempo de resposta.")
    parser.add_argument("--repeticoes", type=int, default=3,
                        help="execuções por combinação de bloco e janela")
    args = parser.parse_args(argv)

    print("Gerando WAV de pior caso (5 min, 48 kHz, estéreo)...")
    dados = wav_pior_caso()
    print(f"Tamanho: {len(dados) / 1e6:.1f} MB\n")

    tempo_upload, api = medir_api(dados, args.repeticoes)
    print(f"Upload (POST /api/audios): {tempo_upload:.3f} s\n")
    print("Tabela 1 - POST /api/analyses (NF004: até 2 s)")
    imprimir_tabela(api)

    print("\nTabela 2 - DFT direta x FFT própria (um bloco)")
    bench = medir_dft_fft()
    imprimir_tabela(bench)

    salvar_csv(PASTA_SAIDA / "tempo_resposta.csv", api)
    salvar_csv(PASTA_SAIDA / "dft_fft.csv", bench)
    print(f"\nResultados salvos em {PASTA_SAIDA}")

    pior = max(linha["max_s"] for linha in api)
    if pior > LIMITE_S:
        print(f"\nNF004 NÃO atendido: pior caso {pior:.3f} s > {LIMITE_S} s")
        return 1
    print(f"\nNF004 atendido: pior caso {pior:.3f} s <= {LIMITE_S} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())