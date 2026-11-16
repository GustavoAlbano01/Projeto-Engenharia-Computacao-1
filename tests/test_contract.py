"""Testes do contrato da API v1: formato das respostas e dos erros."""
import io
import wave

from app.contract import MAX_UPLOAD_BYTES


def make_wav(num_samples=8000, rate=8000):
    """WAV PCM 16 bits mono de verdade (silêncio), montado em memória."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * num_samples)
    return buf.getvalue()


VALID_WAV = make_wav()


def upload(client, name="tom.wav", data=VALID_WAV):
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

def test_analise_audio_curto(client):
    """Fluxo alternativo do RF002: menos de 512 amostras."""
    audio_id = upload(client, data=make_wav(num_samples=400)).get_json()["id"]
    resp = analyze(client, audio_id=audio_id, block_size=512, window="hanning")
    assert_error(resp, 400, "AUDIO_TOO_SHORT")


def test_analise_bloco_ajustado_pela_api(client):
    """Fluxo alternativo do RF002: bloco maior que o áudio."""
    audio_id = upload(client, data=make_wav(num_samples=3000)).get_json()["id"]
    resp = analyze(client, audio_id=audio_id, block_size=4096, window="hanning")
    assert resp.status_code == 201
    a = resp.get_json()
    assert a["params"]["block_size"] == 2048
    assert a["warnings"][0]["code"] == "BLOCK_SIZE_ADJUSTED"
    assert len(a["magnitudes"]) == 2048 // 2 + 1



# ---------- T26: GET /api/analyses e GET /api/analyses/{id} ----------
def test_historico_mais_recente_primeiro(client):
    audio_id = upload(client).get_json()["id"]
    ids = [analyze(client, audio_id=audio_id, block_size=b,
                   window="hanning").get_json()["id"]
           for b in (512, 1024, 2048)]
    lista = client.get("/api/analyses").get_json()
    assert [a["id"] for a in lista] == list(reversed(ids))


def test_historico_campos_do_resumo(client):
    audio_id = upload(client).get_json()["id"]
    analyze(client, audio_id=audio_id, block_size=1024, window="hanning")
    resumo = client.get("/api/analyses").get_json()[0]
    assert set(resumo) == {"id", "created_at", "audio", "params", "peak"}
    assert set(resumo["audio"]) == {"id", "filename"}
    assert set(resumo["params"]) == {"block_size", "window"}
    assert set(resumo["peak"]) == {"frequency_hz", "magnitude"}


def test_get_por_id_igual_ao_post(client):
    audio_id = upload(client).get_json()["id"]
    criada = analyze(client, audio_id=audio_id, block_size=1024,
                     window="hamming").get_json()
    lida = client.get(f"/api/analyses/{criada['id']}").get_json()
    assert lida == criada


def test_get_por_id_inexistente(client):
    assert_error(client.get("/api/analyses/999"), 404, "ANALYSIS_NOT_FOUND")


def test_historico_continua_depois_de_reiniciar(tmp_path):
    """NF007: o histórico fica no SQLite, não na memória do servidor."""
    from app import create_app
    db_url = f"sqlite:///{tmp_path / 'aea.db'}"
    pasta = tmp_path / "uploads"

    primeiro = create_app(upload_dir=pasta, db_url=db_url).test_client()
    audio_id = upload(primeiro).get_json()["id"]
    criada = analyze(primeiro, audio_id=audio_id, block_size=1024,
                     window="hanning").get_json()

    reiniciado = create_app(upload_dir=pasta, db_url=db_url).test_client()
    assert [a["id"] for a in reiniciado.get("/api/analyses").get_json()] == [criada["id"]]
    assert reiniciado.get(f"/api/analyses/{criada['id']}").get_json() == criada



# ---------- T29: GET /api/analyses/{id}/spectrogram ----------
def test_espectrograma_png(client):
    audio_id = upload(client).get_json()["id"]
    analise = analyze(client, audio_id=audio_id, block_size=1024,
                      window="hanning").get_json()
    resp = client.get(f"/api/analyses/{analise['id']}/spectrogram")
    assert resp.status_code == 200
    assert resp.mimetype == "image/png"
    assert resp.data[:8] == b"\x89PNG\r\n\x1a\n"


def test_espectrograma_analise_inexistente(client):
    assert_error(client.get("/api/analyses/999/spectrogram"), 404,
                 "ANALYSIS_NOT_FOUND")


def test_espectrograma_wav_apagado_do_disco(client, tmp_path):
    audio_id = upload(client).get_json()["id"]
    analise = analyze(client, audio_id=audio_id, block_size=1024,
                      window="hanning").get_json()
    for arquivo in (tmp_path / "uploads").iterdir():
        arquivo.unlink()
    assert_error(client.get(f"/api/analyses/{analise['id']}/spectrogram"),
                 404, "AUDIO_NOT_FOUND")
    
# ---------- T30: mensagens de erro claras (NF002) ----------
def test_erro_de_banco_tem_mensagem_clara(client):
    from sqlalchemy.exc import OperationalError

    def banco_travado(*args, **kwargs):
        raise OperationalError("SELECT", {}, Exception("database is locked"))

    client.application.extensions["store"].list_summaries = banco_travado
    resp = client.get("/api/analyses")
    assert_error(resp, 500, "INTERNAL_ERROR")
    assert "banco de dados" in resp.get_json()["error"]["message"]


def test_upload_sem_arquivo_sem_jargao(client):
    resp = client.post("/api/audios", data={},
                       content_type="multipart/form-data")
    assert_error(resp, 400, "FILE_MISSING")
    assert "'file'" not in resp.get_json()["error"]["message"]


def test_endereco_inexistente(client):
    resp = client.get("/api/nao-existe")
    assert resp.status_code == 404
    assert resp.get_json()["error"]["message"] == "Endereço não encontrado."