"""Testes do experimento de vazamento espectral (T33).

Os valores de referência são os de Harris (1978) para um tom no meio de
dois bins (perda de amplitude no pior caso).
"""
import csv
import pytest
from tools.experimento_vazamento import main, rodar

@pytest.fixture(scope="module")
def resultado():
    linhas, espectros = rodar(duracao_s=1.0)
    por_chave = {(linha["tom"], linha["janela"]): linha for linha in linhas}
    return por_chave, espectros


def test_tom_no_centro_do_bin_nao_perde_amplitude(resultado):
    linhas, _ = resultado
    for janela in ("rectangular", "hanning", "hamming"):
        linha = linhas[("centro do bin", janela)]
        assert linha["magnitude_pico"] == pytest.approx(0.5, abs=0.001)


@pytest.mark.parametrize("janela, perda_db", [
    ("rectangular", -3.92),   # 20·log10(2/π)
    ("hanning", -1.42),
    ("hamming", -1.75),
])
def test_perda_no_pior_caso_igual_a_teoria(resultado, janela, perda_db):
    linhas, _ = resultado
    linha = linhas[("entre dois bins", janela)]
    assert linha["perda_amplitude_db"] == pytest.approx(perda_db, abs=0.05)


def test_janelas_reduzem_o_vazamento_longe_do_pico(resultado):
    linhas, _ = resultado
    nivel = {j: linhas[("entre dois bins", j)]["nivel_30_bins_db"]
             for j in ("rectangular", "hanning", "hamming")}
    assert nivel["hanning"] < nivel["hamming"] < nivel["rectangular"]


def test_retangular_espalha_mais_energia(resultado):
    linhas, _ = resultado
    espalhamento = {j: linhas[("entre dois bins", j)]
                    ["bins_acima_de_menos_40db"]
                    for j in ("rectangular", "hanning", "hamming")}
    assert espalhamento["rectangular"] > 5 * espalhamento["hanning"]


def test_main_grava_csv_e_figura(tmp_path):
    assert main(["--saida", str(tmp_path)]) == 0
    with open(tmp_path / "vazamento.csv", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 6      # 2 tons x 3 janelas
    figura = tmp_path / "figura1_vazamento.png"
    assert figura.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"