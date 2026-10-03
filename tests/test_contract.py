"""Testes do contrato da API v1: formato das respostas e dos erros."""
import io

from app.contract import MAX_UPLOAD_BYTES

FAKE_WAV = b"RIFF" + b"\x00" * 100


def upload(client, name="tom.wav", data=FAKE_WAV):
    return client.post("/api/audios",
                       data={"file": (io.BytesIO(data), name)},
                       content_type="multipart/form-data")


def analyze(client, **body):
    return client.post("/api/analyses", json=body)


def assert_error(resp, status, code):
    assert resp.status_code == status
    body = resp.get_json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert body["error"]["message"]


# ---------- RF001 ----------
def test_upload_ok(client):
    resp = upload(client)
    assert resp.status_code == 201
    audio = resp.get_json()
    for key in ("id", "filename", "sample_rate_hz", "channels",
                "num_samples", "duration_s", "uploaded_at"):
        assert key in audio


def test_upload_sem_arquivo(client):
    resp = client.post("/api/audios", data={},
                       content_type="multipart/form-data")
    assert_error(resp, 400, "FILE_MISSING")


def test_upload_mp3(client):
    assert_error(upload(client, name="musica.mp3"), 415, "UNSUPPORTED_FORMAT")


def test_upload_vazio(client):
    assert_error(upload(client, data=b""), 400, "EMPTY_AUDIO")


def test_upload_grande_demais(client):
    big = b"\x00" * (MAX_UPLOAD_BYTES + 1)
    assert_error(upload(client, data=big), 413, "FILE_TOO_LARGE")


# ---------- RF002 / RF003 ----------
def test_analise_ok(client):
    audio_id = upload(client).get_json()["id"]
    resp = analyze(client, audio_id=audio_id, block_size=1024, window="hanning")
    assert resp.status_code == 201
    a = resp.get_json()
    assert len(a["frequencies_hz"]) == len(a["magnitudes"])
    assert a["params"] == {"block_size": 1024, "window": "hanning"}
    assert {"bin", "frequency_hz", "magnitude"} <= set(a["peak"])
    assert isinstance(a["warnings"], list)


def test_analise_bloco_invalido(client):
    audio_id = upload(client).get_json()["id"]
    resp = analyze(client, audio_id=audio_id, block_size=1000, window="hanning")
    assert_error(resp, 400, "INVALID_PARAMETER")


def test_analise_janela_invalida(client):
    audio_id = upload(client).get_json()["id"]
    resp = analyze(client, audio_id=audio_id, block_size=1024, window="blackman")
    assert_error(resp, 400, "INVALID_PARAMETER")


def test_analise_json_malformado(client):
    resp = client.post("/api/analyses", data="{isso não é json",
                       content_type="application/json")
    assert_error(resp, 400, "INVALID_PARAMETER")


def test_analise_audio_inexistente(client):
    resp = analyze(client, audio_id=999, block_size=1024, window="hanning")
    assert_error(resp, 404, "AUDIO_NOT_FOUND")


# ---------- RF007 / RF008 / RF009 ----------
def test_historico_vazio(client):
    resp = client.get("/api/analyses")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_fluxo_historico_completo(client):
    audio_id = upload(client).get_json()["id"]
    created = analyze(client, audio_id=audio_id,
                      block_size=2048, window="hamming").get_json()

    lista = client.get("/api/analyses").get_json()
    assert len(lista) == 1
    assert "magnitudes" not in lista[0]  # resumo não leva vetores

    full = client.get(f"/api/analyses/{created['id']}")
    assert full.status_code == 200
    assert full.get_json()["magnitudes"]

    assert client.delete(f"/api/analyses/{created['id']}").status_code == 204
    assert_error(client.get(f"/api/analyses/{created['id']}"),
                 404, "ANALYSIS_NOT_FOUND")


def test_cors_habilitado(client):
    resp = client.get("/api/analyses", headers={"Origin": "http://localhost:5173"})
    # o Flask-CORS devolve a própria origem quando origins="*"
    assert resp.headers.get("Access-Control-Allow-Origin") is not None
