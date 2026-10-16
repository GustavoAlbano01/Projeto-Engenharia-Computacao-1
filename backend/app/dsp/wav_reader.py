"""Leitor de WAV PCM 16 bits (T11, RF001).

Lê o cabeçalho e as amostras com o módulo wave da biblioteca padrão,
converte estéreo para mono pela média dos canais e devolve os metadados
com os nomes do contrato da API (docs/CONTRATO_API.md).
"""
import wave
from dataclasses import dataclass

import numpy as np

BITS_PER_SAMPLE = 16
SAMPLE_WIDTH_BYTES = BITS_PER_SAMPLE // 8
FULL_SCALE = 32768  # 2^15: -32768 vira -1.0


class WavError(Exception):
    """Base dos erros de leitura. 'code' é o código de erro do contrato."""
    code = "INVALID_WAV"


class InvalidWavError(WavError):
    code = "INVALID_WAV"          # cabeçalho RIFF/WAVE inválido -> 400


class UnsupportedFormatError(WavError):
    code = "UNSUPPORTED_FORMAT"   # WAV válido, mas não PCM 16 bits -> 415


class EmptyAudioError(WavError):
    code = "EMPTY_AUDIO"          # WAV sem amostras -> 400

@dataclass
class WavAudio:
    """Resultado da leitura: amostras mono normalizadas e metadados."""
    samples: np.ndarray   # float64, mono, entre -1 e 1
    sample_rate_hz: int
    channels: int         # canais do arquivo original (1 ou 2)
    num_samples: int      # amostras por canal

    @property
    def duration_s(self):
        return self.num_samples / self.sample_rate_hz

    def metadata(self):
        """Campos do contrato para a resposta de POST /api/audios."""
        return {
            "format": "wav_pcm",
            "bits_per_sample": BITS_PER_SAMPLE,
            "sample_rate_hz": self.sample_rate_hz,
            "channels": self.channels,
            "num_samples": self.num_samples,
            "duration_s": round(self.duration_s, 3),
        }

def read_wav(source):
    """Lê um WAV PCM 16 bits. 'source' é um caminho ou um objeto arquivo."""
    try:
        with wave.open(source, "rb") as w:
            channels = w.getnchannels()
            sample_width = w.getsampwidth()
            sample_rate = w.getframerate()
            raw = w.readframes(w.getnframes())
    except wave.Error as err:
        if str(err).startswith("unknown format"):
            raise UnsupportedFormatError(
                "WAV não PCM (ex.: ponto flutuante ou compactado).") from err
        raise InvalidWavError(f"Cabeçalho WAV inválido: {err}") from err
    except EOFError as err:
        raise InvalidWavError("Arquivo WAV truncado ou corrompido.") from err

    if sample_width != SAMPLE_WIDTH_BYTES:
        raise UnsupportedFormatError(
            f"WAV de {sample_width * 8} bits; só 16 bits é aceito.")
    if channels not in (1, 2):
        raise UnsupportedFormatError(
            f"WAV com {channels} canais; só mono ou estéreo.")
    if sample_rate <= 0:
        raise InvalidWavError("Taxa de amostragem inválida no cabeçalho.")

    # Usa só os quadros completos (o cabeçalho pode prometer mais do que há).
    frame_bytes = sample_width * channels
    num_samples = len(raw) // frame_bytes
    if num_samples == 0:
        raise EmptyAudioError("O WAV não tem amostras.")

    # Inteiros de 16 bits little-endian, intercalados: L R L R ...
    pcm = np.frombuffer(raw[:num_samples * frame_bytes], dtype="<i2")
    pcm = pcm.reshape(num_samples, channels)
    samples = pcm.mean(axis=1) / FULL_SCALE   # estéreo -> mono pela média

    return WavAudio(samples, sample_rate, channels, num_samples)