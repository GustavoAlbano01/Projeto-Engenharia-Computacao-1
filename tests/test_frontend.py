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

PLOTLY = "vendor/plotly-2.35.2.min.js"


def test_plotly_local(client):
    resp = client.get("/" + PLOTLY)
    assert resp.status_code == 200
    assert len(resp.data) > 1_000_000      # ~4,5 MB: não é uma página de erro


def test_so_a_tela_de_resultado_carrega_plotly(client):
    """O Plotly (4,5 MB) só é carregado onde há gráfico (INT02)."""
    assert f'src="{PLOTLY}"' in client.get("/resultado.html").get_data(as_text=True)
    for caminho in ("/", "/historico.html"):
        html = client.get(caminho).get_data(as_text=True)
        assert "plotly" not in html, caminho


def test_nenhuma_tela_usa_cdn(client):
    """NF011: nada pode depender de internet."""
    for caminho in ("/", "/historico.html", "/resultado.html"):
        html = client.get(caminho).get_data(as_text=True)
        assert "http://" not in html and "https://" not in html, caminho

def test_nenhum_script_carregado_duas_vezes(client):
    """Carregar o mesmo .js duas vezes gera 'Identifier already declared'."""
    import re
    for caminho in ("/", "/historico.html", "/resultado.html"):
        html = client.get(caminho).get_data(as_text=True)
        scripts = re.findall(r'<script src="([^"]+)"', html)
        assert len(scripts) == len(set(scripts)), (caminho, scripts)

# ---------- INT01 (T23) ----------
def test_int01_campos_do_formulario(client):
    html = client.get("/").get_data(as_text=True)
    assert 'type="file" id="arquivo" accept=".wav"' in html
    for valor in ("512", "1024", "2048", "4096"):
        assert f'<option value="{valor}"' in html
    for valor in ("rectangular", "hanning", "hamming"):
        assert f'<option value="{valor}"' in html
    assert 'id="analisar" disabled' in html          # crítica da INT01
    assert 'href="historico.html"' in html