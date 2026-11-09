import numpy as np
import pytest

from app.dsp.analysis import (AudioTooShortError, analyze, block_starts,
                              choose_block_size)

FS = 44100


def tone(freq, seconds, amp=0.5):
    """Senoide de teste com amplitude 'amp'."""
    t = np.arange(int(FS * seconds)) / FS
    return amp * np.sin(2 * np.pi * freq * t)

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

# ---------- block_starts ----------
def test_blocos_sem_sobreposicao():
    starts = block_starts(10_000, 2048)
    assert list(starts) == [0, 2651, 5301, 7952]
    assert np.all(np.diff(starts) >= 2048)


def test_ultimo_bloco_termina_dentro_do_audio():
    starts = block_starts(10_000, 2048)
    assert starts[-1] + 2048 <= 10_000


def test_maximo_256_blocos():
    assert len(block_starts(FS * 60, 1024)) == 256


def test_um_unico_bloco():
    assert list(block_starts(1500, 1024)) == [0]


# ---------- analyze ----------
def test_tamanho_dos_vetores():
    r = analyze(tone(440, 1), FS, 1024, "hanning")
    assert len(r["frequencies_hz"]) == len(r["magnitudes"]) == 513


def test_tom_440hz_pico_e_amplitude():
    r = analyze(tone(440, 3), FS, 1024, "hanning")
    df = FS / 1024                                       # ≈ 43,07 Hz
    assert abs(r["peak"]["frequency_hz"] - 440) <= df
    assert r["peak"]["magnitude"] == pytest.approx(0.5, abs=0.05)


def test_tom_exato_no_bin_amplitude_exata():
    # f = 10 · fs / N: cabem exatamente 10 ciclos em cada bloco
    f = 10 * FS / 1024
    r = analyze(tone(f, 2), FS, 1024, "rectangular")
    assert r["peak"]["bin"] == 10
    assert r["peak"]["magnitude"] == pytest.approx(0.5, abs=1e-6)


def test_bloco_ajustado_aparece_no_resultado():
    r = analyze(tone(1000, 0.07), FS, 4096, "rectangular")  # ~3087 amostras
    assert r["params"]["block_size"] == 2048
    assert r["warnings"][0]["code"] == "BLOCK_SIZE_ADJUSTED"


def test_silencio_nao_quebra():
    r = analyze(np.zeros(8000), 8000, 512, "hamming")
    assert max(r["magnitudes"]) == 0.0