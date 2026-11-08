"""Testes do ajuste do tamanho de bloco (T18, RF002)."""
import pytest

from app.dsp.analysis import AudioTooShortError, choose_block_size


def test_bloco_cabe_nao_ajusta():
    assert choose_block_size(1024, 5000) == (1024, [])


def test_bloco_maior_que_audio_ajusta():
    used, warnings = choose_block_size(4096, 3000)
    assert used == 2048
    assert len(warnings) == 1
    assert warnings[0]["code"] == "BLOCK_SIZE_ADJUSTED"
    assert warnings[0]["details"] == {"requested": 4096, "used": 2048}
    assert warnings[0]["message"]          # mensagem não vazia (NF002)


def test_audio_menor_que_512_e_erro():
    with pytest.raises(AudioTooShortError):
        choose_block_size(512, 400)


def test_bloco_exatamente_igual_ao_audio():
    assert choose_block_size(1024, 1024) == (1024, [])   # cabe, não ajusta


def test_audio_com_exatamente_512():
    used, warnings = choose_block_size(4096, 512)
    assert used == 512 and len(warnings) == 1