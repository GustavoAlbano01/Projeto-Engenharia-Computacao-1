"""RF002/RF003 (POST), RF007 (GET lista), RF008 (GET id), RF009 (DELETE), RF006."""
from flask import Blueprint, current_app, jsonify, request

from ..contract import BLOCK_SIZES, WINDOWS
from ..errors import ApiError

bp = Blueprint("analyses", __name__)


def _store():
    return current_app.extensions["store"]


def _get_analysis_or_404(analysis_id):
    analysis = _store().analyses.get(analysis_id)
    if analysis is None:
        raise ApiError(404, "ANALYSIS_NOT_FOUND",
                       "Análise não encontrada.", {"id": analysis_id})
    return analysis


def _validate_params(body):
    """Confere o corpo do POST e devolve (audio_id, block_size, window)."""
    if not isinstance(body, dict):
        raise ApiError(400, "INVALID_PARAMETER",
                       "O corpo da requisição deve ser um JSON válido.")

    audio_id = body.get("audio_id")
    block_size = body.get("block_size")
    window = body.get("window")

    # bool é subclasse de int em Python, por isso a checagem extra
    if not isinstance(audio_id, int) or isinstance(audio_id, bool):
        raise ApiError(400, "INVALID_PARAMETER",
                       "O campo 'audio_id' é obrigatório e deve ser inteiro.")
    if block_size not in BLOCK_SIZES or isinstance(block_size, bool):
        raise ApiError(400, "INVALID_PARAMETER",
                       "Tamanho de bloco inválido.",
                       {"field": "block_size", "allowed": list(BLOCK_SIZES)})
    if window not in WINDOWS:
        raise ApiError(400, "INVALID_PARAMETER",
                       "Função de janelamento inválida.",
                       {"field": "window", "allowed": list(WINDOWS)})
    return audio_id, block_size, window


@bp.post("")
def create_analysis():
    body = request.get_json(silent=True)
    audio_id, block_size, window = _validate_params(body)

    audio = _store().audios.get(audio_id)
    if audio is None:
        raise ApiError(404, "AUDIO_NOT_FOUND",
                       "Áudio não encontrado. Envie o arquivo novamente.",
                       {"audio_id": audio_id})

    # TODO (tarefa FFT): janelamento + FFT radix-2 + média de até 256 blocos.
    # TODO (tarefa FFT): se o áudio tiver menos de 512 amostras, lançar
    # ApiError(400, "AUDIO_TOO_SHORT", ...) conforme o contrato (RF002).
    analysis = _store().add_analysis(audio, block_size, window)
    return jsonify(analysis), 201


@bp.get("")
def list_analyses():
    return jsonify(_store().list_summaries()), 200


@bp.get("/<int:analysis_id>")
def get_analysis(analysis_id):
    return jsonify(_get_analysis_or_404(analysis_id)), 200


@bp.delete("/<int:analysis_id>")
def delete_analysis(analysis_id):
    _get_analysis_or_404(analysis_id)
    del _store().analyses[analysis_id]
    return "", 204


@bp.get("/<int:analysis_id>/spectrogram")
def get_spectrogram(analysis_id):
    _get_analysis_or_404(analysis_id)
    # RF006 é desejável: só depois dos essenciais.
    raise ApiError(501, "NOT_IMPLEMENTED",
                   "Espectrograma ainda não implementado.")
