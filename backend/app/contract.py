"""Constantes do contrato da API v1 (docs/CONTRATO_API.md).

Ficam num lugar só para que validação, testes e documentação
usem exatamente os mesmos valores.
"""
WINDOWS = ("rectangular", "hanning", "hamming")
BLOCK_SIZES = (512, 1024, 2048, 4096)
MAX_UPLOAD_BYTES = 60 * 1024 * 1024  # 60 MB
ALLOWED_EXTENSION = ".wav"
