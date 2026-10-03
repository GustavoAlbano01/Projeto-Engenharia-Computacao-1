"""Envelope único de erro: {"error": {"code", "message", "details"}}.

Toda falha da API passa por aqui (NF002 e NF003): nenhuma exceção
derruba o servidor, todas viram JSON com código HTTP adequado.
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Erro previsto pela API. Lançar com: raise ApiError(400, "CODE", "msg")."""

    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def error_body(code, message, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return jsonify(error_body(err.code, err.message, err.details)), err.status

    @app.errorhandler(413)
    def handle_too_large(_err):
        return jsonify(error_body(
            "FILE_TOO_LARGE",
            "O arquivo excede o limite de 60 MB.",
        )), 413

    @app.errorhandler(HTTPException)
    def handle_http(err):
        # 404 de rota inexistente, 405 de método errado etc.
        return jsonify(error_body(
            "HTTP_" + str(err.code),
            "Requisição inválida para esta rota.",
        )), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception(err)
        return jsonify(error_body(
            "INTERNAL_ERROR",
            "Erro interno no servidor. Tente novamente.",
        )), 500
