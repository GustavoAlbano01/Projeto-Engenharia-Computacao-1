"""O Flask serve o frontend junto com a API (T22 - NF011)."""


def test_raiz_abre_a_tela_inicial(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Analisador Espectral de Áudio" in resp.get_data(as_text=True)


def test_index_html_pelo_nome(client):
    assert client.get("/index.html").status_code == 200


def test_api_continua_funcionando(client):
    resp = client.get("/api/analyses")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_arquivo_inexistente_da_404(client):
    assert client.get("/nao-existe.html").status_code == 404