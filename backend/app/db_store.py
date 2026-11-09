"""Armazenamento no SQLite (T20 - RF003, NF007).

Tem os mesmos métodos que as rotas precisam do MockStore, mas grava
nas tabelas audios e analyses (app/models.py). Devolve sempre
dicionários no formato do contrato (docs/CONTRATO_API.md).
"""
from datetime import timezone

from sqlalchemy import select

from .models import Analysis, Audio


def _iso(dt):
    """Data no formato do contrato: ISO 8601 em UTC, ex. 2026-09-24T14:32:10Z.

    O SQLite não guarda o fuso; o que volta "sem fuso" foi gravado em UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DbStore:
    def __init__(self, session_factory):
        self._sessions = session_factory

    # ---------- conversões para dict (sempre dentro da sessão) ----------
    @staticmethod
    def _audio_dict(a):
        return {
            "id": a.id,
            "filename": a.filename,
            "format": a.format,
            "bits_per_sample": a.bits_per_sample,
            "sample_rate_hz": a.sample_rate_hz,
            "channels": a.channels,
            "num_samples": a.num_samples,
            "duration_s": round(a.duration_s, 3),
            "size_bytes": a.size_bytes,
            "uploaded_at": _iso(a.uploaded_at),
        }

    @staticmethod
    def _analysis_dict(a):
        return {
            "id": a.id,
            "audio": {"id": a.audio.id, "filename": a.audio.filename},
            "created_at": _iso(a.created_at),
            "params": {"block_size": a.block_size, "window": a.window},
            "blocks_used": a.blocks_used,
            "freq_resolution_hz": round(a.freq_resolution_hz, 4),
            "frequencies_hz": [round(f, 2) for f in a.frequencies_hz],
            "magnitudes": a.magnitudes,
            "peak": {
                "bin": a.peak_bin,
                "frequency_hz": a.peak_frequency_hz,
                "magnitude": a.peak_magnitude,
            },
            "warnings": a.warnings,
        }

    # ---------- áudios (RF001) ----------
    def add_audio(self, filename, size_bytes, metadata, stored_path):
        with self._sessions() as s:
            audio = Audio(
                filename=filename,
                stored_path=stored_path,
                format=metadata["format"],
                bits_per_sample=metadata["bits_per_sample"],
                sample_rate_hz=metadata["sample_rate_hz"],
                channels=metadata["channels"],
                num_samples=metadata["num_samples"],
                size_bytes=size_bytes,
            )
            s.add(audio)
            s.commit()          # aqui o SQLite gera o id
            return self._audio_dict(audio)

    def get_audio(self, audio_id):
        with self._sessions() as s:
            audio = s.get(Audio, audio_id)
            return self._audio_dict(audio) if audio else None

    def get_audio_path(self, audio_id):
        with self._sessions() as s:
            audio = s.get(Audio, audio_id)
            return audio.stored_path if audio else None

    # ---------- análises (RF003, RF007, RF008, RF009) ----------
    def add_analysis(self, audio_id, result):
        """'result' é o dicionário devolvido por dsp.analysis.analyze()."""
        with self._sessions() as s:
            analysis = Analysis(
                audio_id=audio_id,
                block_size=result["params"]["block_size"],
                window=result["params"]["window"],
                blocks_used=result["blocks_used"],
                magnitudes=result["magnitudes"],
                peak_bin=result["peak"]["bin"],
                peak_frequency_hz=result["peak"]["frequency_hz"],
                peak_magnitude=result["peak"]["magnitude"],
                warnings=result["warnings"],
            )
            s.add(analysis)
            s.commit()
            return self._analysis_dict(analysis)

    def get_analysis(self, analysis_id):
        with self._sessions() as s:
            analysis = s.get(Analysis, analysis_id)
            return self._analysis_dict(analysis) if analysis else None

    def list_summaries(self):
        """Histórico sem os vetores, mais recente primeiro."""
        with self._sessions() as s:
            query = select(Analysis).order_by(
                Analysis.created_at.desc(), Analysis.id.desc())
            return [
                {
                    "id": a.id,
                    "created_at": _iso(a.created_at),
                    "audio": {"id": a.audio.id, "filename": a.audio.filename},
                    "params": {"block_size": a.block_size, "window": a.window},
                    "peak": {"frequency_hz": a.peak_frequency_hz,
                             "magnitude": a.peak_magnitude},
                }
                for a in s.scalars(query)
            ]

    def delete_analysis(self, analysis_id):
        with self._sessions() as s:
            analysis = s.get(Analysis, analysis_id)
            if analysis is None:
                return False
            s.delete(analysis)
            s.commit()
            return True