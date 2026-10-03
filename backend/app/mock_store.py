"""Armazenamento FALSO, em memória, usado só nesta fase.

Ele permite que o frontend já consuma a API real com dados de mentira.
Será substituído por SQLAlchemy + SQLite (tarefa de persistência) e
pelos módulos de WAV/FFT (tarefas de processamento) sem mudar as rotas.
"""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

MOCKS_DIR = Path(__file__).resolve().parent.parent / "mocks"


def _load(name):
    with open(MOCKS_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class MockStore:
    def __init__(self):
        self._audio_template = _load("audio_upload_201.json")
        self._analysis_template = _load("analysis_create_201.json")
        self.audios = {}
        self.analyses = {}
        self._next_audio_id = 1
        self._next_analysis_id = 1

    def add_audio(self, filename, size_bytes):
        audio = copy.deepcopy(self._audio_template)
        audio.update(
            id=self._next_audio_id,
            filename=filename,
            size_bytes=size_bytes,
            uploaded_at=now_iso(),
        )
        self.audios[audio["id"]] = audio
        self._next_audio_id += 1
        return audio

    def add_analysis(self, audio, block_size, window):
        analysis = copy.deepcopy(self._analysis_template)
        analysis.update(
            id=self._next_analysis_id,
            audio={"id": audio["id"], "filename": audio["filename"]},
            created_at=now_iso(),
            params={"block_size": block_size, "window": window},
        )
        self.analyses[analysis["id"]] = analysis
        self._next_analysis_id += 1
        return analysis

    def list_summaries(self):
        items = sorted(self.analyses.values(),
                       key=lambda a: a["created_at"], reverse=True)
        return [
            {
                "id": a["id"],
                "created_at": a["created_at"],
                "audio": a["audio"],
                "params": a["params"],
                "peak": {
                    "frequency_hz": a["peak"]["frequency_hz"],
                    "magnitude": a["peak"]["magnitude"],
                },
            }
            for a in items
        ]
