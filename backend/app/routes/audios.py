"""RF001 - POST /api/audios (T12).

Recebe um WAV, valida extensão, tamanho e conteúdo, salva o arquivo em
backend/uploads/ e devolve os metadados reais (docs/CONTRATO_API.md).
"""
import io
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from ..contract import ALLOWED_EXTENSION
from ..dsp.wav_reader import UnsupportedFormatError, WavError, read_wav
from ..errors import ApiError

bp = Blueprint("audios", __name__)

# Mensagens para o usuário (NF002), uma por código de erro do leitor.
WAV_ERROR_MESSAGES = {
    "INVALID_WAV": "O arquivo está corrompido ou não é um WAV válido.",
    "UNSUPPORTED_FORMAT": "Formato não suportado. Envie um arquivo WAV PCM de 16 bits.",
    "EMPTY_AUDIO": "O arquivo WAV não contém amostras de áudio.",
}


@bp.post("")
def upload_audio():
    # 1. O arquivo veio no campo "file"?
    file = request.files.get("file")
    if file is None or file.filename == "":
        raise ApiError(400, "FILE_MISSING",
                       "Nenhum arquivo foi enviado no campo 'file'.")

    # 2. A extensão é .wav?
    filename = file.filename
    extension = Path(filename).suffix.lower()
    if extension != ALLOWED_EXTENSION:
        raise ApiError(415, "UNSUPPORTED_FORMAT",
                       WAV_ERROR_MESSAGES["UNSUPPORTED_FORMAT"],
                       {"received_extension": extension or None})

    # 3. O limite de 60 MB (NF006) é checado pelo Flask antes de chegar aqui:
    #    MAX_CONTENT_LENGTH em create_app() -> erro 413 FILE_TOO_LARGE.

    # 4. O arquivo tem algum byte?
    data = file.read()
    if len(data) == 0:
        raise ApiError(400, "EMPTY_AUDIO", "O arquivo enviado está vazio.")

    # 5. O conteúdo é um WAV PCM 16 bits de verdade? (leitor do T11)
    try:
        audio = read_wav(io.BytesIO(data))
    except WavError as err:
        status = 415 if isinstance(err, UnsupportedFormatError) else 400
        raise ApiError(status, err.code, WAV_ERROR_MESSAGES[err.code],
                       {"reason": str(err)}) from err

    # 6. Só depois de validado, salva com nome único e seguro.
    stored_name = f"{uuid.uuid4().hex}_{secure_filename(filename) or 'audio.wav'}"
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / stored_name
    stored_path.write_bytes(data)

    # 7. Registra com os metadados reais.
    # TODO (T20): gravar no banco (tabela audios) em vez do armazenamento em memória.
    record = current_app.extensions["store"].add_audio(
        filename=filename,
        size_bytes=len(data),
        metadata=audio.metadata(),
        stored_path=str(stored_path),
    )

    # 8. Responde 201 no formato do contrato.
    return jsonify(record), 201