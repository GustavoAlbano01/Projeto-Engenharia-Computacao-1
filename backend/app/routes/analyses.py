"""RF002/RF003 (POST), RF007 (GET lista), RF008 (GET id), RF009 (DELETE), RF006."""
from flask import Blueprint, current_app, jsonify, request

from ..contract import BLOCK_SIZES, WINDOWS
from ..dsp.analysis import AudioTooShortError, analyze
from ..dsp.wav_reader import read_wav
from ..errors import ApiError

bp = Blueprint("analyses", __name__)


def _store():
    return current_app.extensions["store"]


def _analysis_not_found(analysis_id):
    return ApiError(404, "ANALYSIS_NOT_FOUND",
                    "Análise não encontrada.", {"id": analysis_id})


def _audio_not_found(audio_id):
    return ApiError(404, "AUDIO_NOT_FOUND",
                    "Áudio não encontrado. Envie o arquivo novamente.",
                    {"audio_id": audio_id})


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
    store = _store()

    # 1. O áudio existe no banco?
    path = store.get_audio_path(audio_id)
    if path is None:
        raise _audio_not_found(audio_id)

    # 2. O arquivo ainda existe no disco? (leitor do T11)
    try:
        wav = read_wav(path)
    except FileNotFoundError as err:
        raise _audio_not_found(audio_id) from err

    # 3. Janela + FFT + média dos blocos (T14-T18, T20)
    try:
        result = analyze(wav.samples, wav.sample_rate_hz, block_size, window)
    except AudioTooShortError as err:
        raise ApiError(400, "AUDIO_TOO_SHORT",
                       "O áudio é curto demais para análise "
                       "(mínimo de 512 amostras).",
                       {"reason": str(err)}) from err

    # 4. Grava no banco e responde no formato do contrato
    analysis = store.add_analysis(audio_id, result)
    return jsonify(analysis), 201


@bp.get("")
def list_analyses():
    return jsonify(_store().list_summaries()), 200


@bp.get("/<int:analysis_id>")
def get_analysis(analysis_id):
    analysis = _store().get_analysis(analysis_id)
    if analysis is None:
        raise _analysis_not_found(analysis_id)
    return jsonify(analysis), 200


@bp.delete("/<int:analysis_id>")
def delete_analysis(analysis_id):
    if not _store().delete_analysis(analysis_id):
        raise _analysis_not_found(analysis_id)
    return "", 204


@bp.get("/<int:analysis_id>/spectrogram")
def get_spectrogram(analysis_id):
    if _store().get_analysis(analysis_id) is None:
        raise _analysis_not_found(analysis_id)
    # RF006 é desejável: só depois dos essenciais.
    raise ApiError(501, "NOT_IMPLEMENTED",
                   "Espectrograma ainda não implementado.")