"""Revisão cruzada (T35 - NF009): testes extras do módulo de validação (T32).

Escritos por Eduardo para o módulo do Gustavo (backend/tools/validar_picos.py).
Cobrem o que test_validar_picos.py não cobre: a conta de uma linha isolada
(sem DSP), os dois casos extremos documentados em docs/resultados/README.md
e a gravação do CSV.
"""
import csv

import pytest

from tools.validar_picos import linha_de_resultado, salvar_csv, validar


def _resultado_falso(freq_detectada, n, janela="hanning", magnitude=0.5):
    """Imita o dicionário devolvido por analyze(), sem calcular FFT."""
    return {"peak": {"frequency_hz": freq_detectada, "magnitude": magnitude},
            "params": {"block_size": n, "window": janela}}


# ---------- conta de uma linha, isolada (sem DSP) ----------
def test_linha_calcula_resolucao_erro_e_bins():
    # fs = 8000, N = 1024 -> Δf = 7,8125 Hz. Detectou 437,5 para 440 Hz.
    linha = linha_de_resultado(440.0, 8000, _resultado_falso(437.5, 1024))
    assert linha["resolucao_hz"] == pytest.approx(7.81, abs=0.01)
    assert linha["erro_hz"] == pytest.approx(-2.5)
    assert linha["erro_relativo_pct"] == pytest.approx(2.5 / 440 * 100,
                                                       abs=0.01)
    assert linha["erro_em_bins"] == pytest.approx(2.5 / 7.8125, abs=0.001)
    assert linha["dentro_de_um_bin"] is True


def test_linha_reprova_erro_maior_que_um_bin():
    # Erro de 10 Hz com Δf = 7,81 Hz tem que ser marcado como fora do critério.
    linha = linha_de_resultado(440.0, 8000, _resultado_falso(450.0, 1024))
    assert linha["dentro_de_um_bin"] is False


# ---------- casos extremos documentados no README de resultados ----------
def test_pior_caso_440hz_48khz_n512_perto_de_6_53_por_cento():
    linhas = validar(freqs=(440.0,), taxas=(48000,), blocos=(512,),
                     duracao_s=1.0)
    pior = max(linha["erro_relativo_pct"] for linha in linhas)
    assert pior == pytest.approx(6.53, abs=0.01)
    assert all(linha["resolucao_hz"] == pytest.approx(93.75) for linha in linhas)


def test_1000hz_a_8khz_n4096_cai_exatamente_sobre_um_bin():
    # 1000 / (8000 / 4096) = 512, número inteiro: o pico cai no centro do bin.
    linhas = validar(freqs=(1000.0,), taxas=(8000,), blocos=(4096,),
                     duracao_s=1.0)
    for linha in linhas:
        assert linha["erro_hz"] == pytest.approx(0.0, abs=0.01)


# ---------- gravação do CSV ----------
def test_salvar_csv_cria_pasta_e_mantem_as_colunas(tmp_path):
    linhas = validar(freqs=(440.0,), taxas=(8000,), blocos=(512,),
                     janelas=("hanning",), duracao_s=1.0)
    destino = tmp_path / "nova_pasta" / "saida.csv"
    salvar_csv(destino, linhas)
    with open(destino, encoding="utf-8") as f:
        lidas = list(csv.DictReader(f))
    assert len(lidas) == len(linhas) == 1
    assert list(lidas[0]) == list(linhas[0])