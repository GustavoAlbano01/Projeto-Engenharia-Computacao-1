from flask import Flask
from flask_cors import CORS

from .contract import MAX_UPLOAD_BYTES
from .errors import register_error_handlers
from .mock_store import MockStore
from .routes.analyses import bp as analyses_bp
from .routes.audios import bp as audios_bp


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES  # NF006 -> 413
    app.json.ensure_ascii = False   # acentos legíveis no JSON
    app.json.sort_keys = False      # mantém a ordem do contrato

    CORS(app, resources={r"/api/*": {"origins": "*"}})  # NF008
    app.extensions["store"] = MockStore()

    app.register_blueprint(audios_bp, url_prefix="/api/audios")
    app.register_blueprint(analyses_bp, url_prefix="/api/analyses")
    register_error_handlers(app)
    return app
