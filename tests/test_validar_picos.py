"""Testes do script de validação com sinais de referência (T32)."""
import csv

import pytest

from tools.validar_picos import main, resumo, tabela_artigo, validar


@pytest.fixture(scope="module")
def linhas():
    # Subconjunto pequeno para o teste ser rápido: 1 s de áudio, 2 taxas.
    return validar(taxas=(8000, 44100), duracao_s=1.0)


def test_uma_linha_por_combinacao(linhas):
    # 2 tons x 2 taxas x 3 janelas x 4 blocos
    assert len(linhas) == 2 * 2 * 3 * 4


def test_todos_os_picos_dentro_de_um_bin(linhas):
    for linha in linhas:
        assert linha["dentro_de_um_bin"], linha
        assert abs(linha["erro_hz"]) <= linha["resolucao_hz"] + 0.01


def test_erro_relativo_coerente(linhas):
    for linha in linhas:
        esperado = abs(linha["erro_hz"]) / linha["frequencia_real_hz"] * 100
        assert linha["erro_relativo_pct"] == pytest.approx(esperado, abs=0.01)


def test_tabela_do_artigo_tem_as_colunas_da_tabela_1(linhas):
    artigo = tabela_artigo(linhas, taxa=44100)
    assert len(artigo) == 2 * 3 * 4
    assert list(artigo[0]) == [
        "frequencia_real_hz", "janela", "n", "frequencia_detectada_hz",
        "erro_hz", "erro_relativo_pct"]


def test_resumo_conta_os_casos(linhas):
    r = resumo(linhas)
    assert r["casos"] == len(linhas)
    assert r["dentro_de_um_bin"] == len(linhas)


def test_main_grava_os_dois_csvs(tmp_path):
    assert main(["--saida", str(tmp_path)]) == 0
    with open(tmp_path / "tabela1_artigo.csv", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 24
    assert (tmp_path / "validacao_picos.csv").exists()