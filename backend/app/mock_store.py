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
        self._analysis_template = _load("analysis_create_201.json")
        self.audios = {}
        self.stored_paths = {}  # id do áudio -> caminho do WAV em uploads/
        self.analyses = {}
        self._next_audio_id = 1
        self._next_analysis_id = 1

    def add_audio(self, filename, size_bytes, metadata, stored_path):
        """Guarda um áudio já validado, com os metadados reais do WAV (T12).

        'metadata' vem de WavAudio.metadata(). O caminho do arquivo fica
        guardado à parte porque não faz parte da resposta do contrato.
        """
        audio = {
            "id": self._next_audio_id,
            "filename": filename,
            **metadata,
            "size_bytes": size_bytes,
            "uploaded_at": now_iso(),
        }
        self.audios[audio["id"]] = audio
        self.stored_paths[audio["id"]] = stored_path
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
