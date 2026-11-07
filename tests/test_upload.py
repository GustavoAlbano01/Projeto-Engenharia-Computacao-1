"""Testes do upload de áudio, POST /api/audios (T13 - RF001, NF003).

Os casos básicos de erro (sem arquivo, .mp3, arquivo vazio, maior que
60 MB) já estão em test_contract.py. Aqui ficam os casos que dependem
do conteúdo do WAV e do arquivo salvo em disco.
"""
import io
import wave
from pathlib import Path


def make_wav(num_samples=44100, rate=44100, channels=1, sample_width=2):
    """Monta um WAV (silêncio) em memória e devolve os bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(rate)
        w.writeframes(b"\x00" * sample_width * channels * num_samples)
    return buf.getvalue()


def upload(client, data, name="tom.wav"):
    return client.post("/api/audios",
                       data={"file": (io.BytesIO(data), name)},
                       content_type="multipart/form-data")


def upload_dir(client):
    """Pasta temporária de uploads usada pelo client (ver conftest.py)."""
    return Path(client.application.config["UPLOAD_DIR"])


def saved_files(client):
    folder = upload_dir(client)
    return list(folder.iterdir()) if folder.exists() else []


def assert_error(resp, status, code):
    assert resp.status_code == status
    assert resp.get_json()["error"]["code"] == code


# ---------- WAV válido ----------
def test_mono_devolve_metadados_reais(client):
    data = make_wav(num_samples=88200, rate=44100)   # 2 s
    resp = upload(client, data)

    assert resp.status_code == 201
    audio = resp.get_json()
    assert audio["format"] == "wav_pcm"
    assert audio["bits_per_sample"] == 16
    assert audio["sample_rate_hz"] == 44100
    assert audio["channels"] == 1
    assert audio["num_samples"] == 88200
    assert audio["duration_s"] == 2.0
    assert audio["size_bytes"] == len(data)


def test_estereo_conta_amostras_por_canal(client):
    resp = upload(client, make_wav(num_samples=8000, rate=8000, channels=2))

    assert resp.status_code == 201
    audio = resp.get_json()
    assert audio["channels"] == 2
    assert audio["num_samples"] == 8000   # por canal, não 16000
    assert audio["duration_s"] == 1.0


def test_extensao_maiuscula_aceita(client):
    assert upload(client, make_wav(), name="TOM.WAV").status_code == 201


def test_ids_sao_sequenciais(client):
    first = upload(client, make_wav()).get_json()["id"]
    second = upload(client, make_wav()).get_json()["id"]
    assert second == first + 1


def test_resposta_nao_expoe_caminho_do_arquivo(client):
    audio = upload(client, make_wav()).get_json()
    assert "stored_path" not in audio


# ---------- arquivo salvo em disco ----------
def test_arquivo_salvo_com_mesmo_conteudo(client):
    data = make_wav()
    upload(client, data)

    files = saved_files(client)
    assert len(files) == 1
    assert files[0].read_bytes() == data
    assert files[0].name.endswith("_tom.wav")


def test_mesmo_nome_nao_sobrescreve(client):
    upload(client, make_wav(num_samples=100))
    upload(client, make_wav(num_samples=200))
    assert len(saved_files(client)) == 2


def test_nome_malicioso_fica_dentro_da_pasta(client):
    resp = upload(client, make_wav(), name="../../app.wav")

    assert resp.status_code == 201
    files = saved_files(client)
    assert len(files) == 1
    assert files[0].parent == upload_dir(client)
    assert ".." not in files[0].name


# ---------- WAV inválido ----------
def test_wav_8_bits_recusado(client):
    resp = upload(client, make_wav(sample_width=1))
    assert_error(resp, 415, "UNSUPPORTED_FORMAT")


def test_wav_24_bits_recusado(client):
    resp = upload(client, make_wav(sample_width=3))
    assert_error(resp, 415, "UNSUPPORTED_FORMAT")


def test_arquivo_corrompido(client):
    resp = upload(client, b"RIFF" + b"\x00" * 100)
    assert_error(resp, 400, "INVALID_WAV")


def test_texto_renomeado_para_wav(client):
    resp = upload(client, "isto não é áudio".encode("utf-8"), name="falso.wav")
    assert_error(resp, 400, "INVALID_WAV")


def test_cabecalho_sem_amostras(client):
    resp = upload(client, make_wav(num_samples=0))
    assert_error(resp, 400, "EMPTY_AUDIO")


def test_erro_traz_mensagem_e_motivo(client):
    error = upload(client, make_wav(sample_width=1)).get_json()["error"]
    assert error["message"]                # texto para o usuário (NF002)
    assert error["details"]["reason"]      # detalhe técnico do leitor


def test_arquivo_invalido_nao_e_salvo(client):
    upload(client, b"RIFF" + b"\x00" * 100)
    upload(client, make_wav(sample_width=1))
    upload(client, make_wav(num_samples=0))
    assert saved_files(client) == []