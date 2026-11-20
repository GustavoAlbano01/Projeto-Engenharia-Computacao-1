"""Testes do benchmark DFT x FFT (T34).

Os tempos dependem do computador, então os testes não exigem valores de
tempo: conferem o cálculo da inclinação com dados sintéticos e se o
script gera os arquivos com um benchmark pequeno e rápido.
"""
import csv
import math

import pytest

from tools.benchmark_dft_fft import inclinacao, main, medir

NS = [2 ** k for k in range(8, 14)]


def test_inclinacao_de_n_ao_quadrado_e_2():
    assert inclinacao(NS, [n ** 2 for n in NS]) == pytest.approx(2.0)


def test_inclinacao_de_n_log_n_fica_pouco_acima_de_1():
    a = inclinacao(NS, [n * math.log2(n) for n in NS])
    assert 1.0 < a < 1.2


def test_medir_uma_linha_por_n():
    linhas = medir(ns_dft=[64, 128], ns_fft=[64, 128, 256], repeticoes=1)
    assert [r["n"] for r in linhas] == [64, 128, 256]
    assert linhas[-1]["dft_ms"] is None          # DFT só até 128
    assert all(r["fft_ms"] > 0 for r in linhas)
    assert linhas[0]["razao_teorica"] == pytest.approx(64 / 6, abs=0.1)


def test_main_grava_csv_resumo_e_figura(tmp_path):
    args = ["--saida", str(tmp_path), "--n-max-dft", "2048",
            "--n-max-fft", "8192", "--repeticoes", "1"]
    assert main(args) == 0
    with open(tmp_path / "benchmark_dft_fft.csv", encoding="utf-8") as f:
        assert [int(r["n"]) for r in csv.DictReader(f)][-1] == 8192
    resumo = (tmp_path / "benchmark_dft_fft.md").read_text(encoding="utf-8")
    assert "Ordem de crescimento" in resumo
    figura = tmp_path / "figura2_dft_fft.png"
    assert figura.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"