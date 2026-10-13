"""Testes do gerador de sinais de teste (T10).

O numpy.fft é usado aqui só como referência para conferir os arquivos
gerados; a FFT do sistema é a implementação própria.
"""
import csv
import wave

import numpy as np
import pytest

from tools.gerar_sinais import SINAIS, gerar_amostras, gerar_todos

TAXAS = (8000, 44100)
DURACAO_S = 1.0
N = 4096


def ler_wav(caminho):
    with wave.open(str(caminho), "rb") as w:
        params = (w.getnchannels(), w.getsampwidth(), w.getframerate(),
                  w.getnframes())
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32767
    return params, x


def espectro(x):
    """Magnitude normalizada (Hanning) do primeiro bloco de N amostras."""
    janela = np.hanning(N)
    m = np.abs(np.fft.rfft(x[:N] * janela)) / janela.sum()
    m[1:-1] *= 2
    return m


@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("sinais")
    gerar_todos(pasta, TAXAS, DURACAO_S)
    return pasta


def test_gera_um_arquivo_por_sinal_e_taxa(pasta):
    wavs = sorted(p.name for p in pasta.glob("*.wav"))
    assert len(wavs) == len(SINAIS) * len(TAXAS)
    assert "tom_440hz_44100.wav" in wavs
    assert "dois_tons_440_1000hz_8000.wav" in wavs


@pytest.mark.parametrize("taxa", TAXAS)
def test_formato_wav_pcm16_mono(pasta, taxa):
    params, _ = ler_wav(pasta / f"tom_440hz_{taxa}.wav")
    assert params == (1, 2, taxa, int(taxa * DURACAO_S))


@pytest.mark.parametrize("taxa", TAXAS)
@pytest.mark.parametrize("freq", (440, 1000))
def test_pico_do_tom_puro_dentro_de_um_bin(pasta, taxa, freq):
    _, x = ler_wav(pasta / f"tom_{freq}hz_{taxa}.wav")
    m = espectro(x)
    pico_hz = (np.argmax(m[1:]) + 1) * taxa / N
    assert abs(pico_hz - freq) <= taxa / N
    assert m.max() == pytest.approx(0.5, abs=0.1)  # amplitude do tom


@pytest.mark.parametrize("taxa", TAXAS)
def test_dois_tons_tem_os_dois_picos(pasta, taxa):
    _, x = ler_wav(pasta / f"dois_tons_440_1000hz_{taxa}.wav")
    m = espectro(x)
    resto = m.copy()
    for freq in (440, 1000):
        k = round(freq * N / taxa)
        assert m[k - 1:k + 2].max() == pytest.approx(0.4, abs=0.08)
        resto[k - 3:k + 4] = 0
    assert resto.max() < 0.05  # nenhum outro pico relevante


def test_sinal_nao_satura(pasta):
    _, x = ler_wav(pasta / "dois_tons_440_1000hz_44100.wav")
    assert np.abs(x).max() < 1


def test_csv_lista_os_arquivos(pasta):
    with open(pasta / "sinais.csv", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == len(SINAIS) * len(TAXAS)
    assert {"arquivo", "taxa_hz", "frequencias_hz"} <= set(linhas[0])


def test_recusa_frequencia_acima_de_nyquist():
    with pytest.raises(ValueError):
        gerar_amostras((5000.0,), (0.5,), 8000, DURACAO_S)