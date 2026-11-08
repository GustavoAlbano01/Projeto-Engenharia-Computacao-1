def test_bloco_exatamente_igual_ao_audio():
    assert choose_block_size(1024, 1024) == (1024, [])   # cabe, não ajusta


def test_audio_com_exatamente_512():
    used, warnings = choose_block_size(4096, 512)
    assert used == 512 and len(warnings) == 1