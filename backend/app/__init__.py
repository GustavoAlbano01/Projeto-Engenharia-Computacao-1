from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS

from .contract import MAX_UPLOAD_BYTES
from .database import (DB_PATH, DEFAULT_DB_URL, create_tables, make_engine,
                       make_session_factory)
from .db_store import DbStore
from .errors import register_error_handlers
from .routes.analyses import bp as analyses_bp
from .routes.audios import bp as audios_bp

DEFAULT_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"

# Pasta frontend/ na raiz do repositório (T22 - NF011)
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

def create_app(upload_dir=None, db_url=None):
    """Cria a aplicação.

    Os testes passam 'upload_dir' (pasta temporária) e 'db_url'
    ("sqlite:///:memory:") para não mexer nos dados reais.
    """
    # O Flask também serve o frontend: http://localhost:5000/ abre a
    # interface, e as rotas /api continuam iguais (T22 - NF011).
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES  # NF006 -> 413
    app.config["UPLOAD_DIR"] = str(upload_dir or DEFAULT_UPLOAD_DIR)
    app.json.ensure_ascii = False   # acentos legíveis no JSON
    app.json.sort_keys = False      # mantém a ordem do contrato

    CORS(app, resources={r"/api/*": {"origins": "*"}})  # NF008

    # Banco SQLite (NF007, NF010): cria as tabelas que faltarem.
    if db_url is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        db_url = DEFAULT_DB_URL
    engine = make_engine(db_url)
    create_tables(engine)
    app.extensions["store"] = DbStore(make_session_factory(engine))

    app.register_blueprint(audios_bp, url_prefix="/api/audios")
    app.register_blueprint(analyses_bp, url_prefix="/api/analyses")
    register_error_handlers(app)

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app