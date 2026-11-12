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

def test_telas_e_estilo(client):
    for caminho in ("/historico.html", "/resultado.html", "/css/estilo.css"):
        assert client.get(caminho).status_code == 200, caminho


def test_paginas_usam_o_estilo_comum(client):
    for caminho in ("/", "/historico.html", "/resultado.html"):
        html = client.get(caminho).get_data(as_text=True)
        assert 'href="css/estilo.css"' in html, caminho

def test_scripts_comuns(client):
    for caminho in ("/js/api.js", "/js/comum.js"):
        assert client.get(caminho).status_code == 200, caminho


def test_paginas_carregam_os_scripts_comuns(client):
    for caminho in ("/", "/historico.html", "/resultado.html"):
        html = client.get(caminho).get_data(as_text=True)
        assert 'src="js/api.js"' in html, caminho
        assert 'src="js/comum.js"' in html, caminho