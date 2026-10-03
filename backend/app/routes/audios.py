"""RF001 - POST /api/audios"""
from flask import Blueprint, current_app, jsonify, request

from ..contract import ALLOWED_EXTENSION
from ..errors import ApiError

bp = Blueprint("audios", __name__)


@bp.post("")
def upload_audio():
    file = request.files.get("file")
    if file is None or file.filename == "":
        raise ApiError(400, "FILE_MISSING",
                       "Nenhum arquivo foi enviado no campo 'file'.")

    filename = file.filename
    extension = filename[filename.rfind("."):].lower() if "." in filename else ""
    if extension != ALLOWED_EXTENSION:
        raise ApiError(415, "UNSUPPORTED_FORMAT",
                       "Formato não suportado. Envie um arquivo WAV PCM de 16 bits.",
                       {"received_extension": extension or None})

    data = file.read()
    if len(data) == 0:
        raise ApiError(400, "EMPTY_AUDIO", "O arquivo enviado está vazio.")

    # TODO (tarefa de leitura WAV): validar cabeçalho RIFF/WAVE, PCM 16 bits,
    # extrair metadados reais. Por enquanto devolve metadados do mock.
    audio = current_app.extensions["store"].add_audio(filename, len(data))
    return jsonify(audio), 201
