"""Modelos do banco: tabelas audios e analyses (T09 - RF003, NF007).

Os nomes das colunas seguem o contrato da API (docs/CONTRATO_API.md):
inglês, snake_case e unidade no nome.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Audio(Base):
    """Arquivo WAV enviado pelo usuário (RF001)."""

    __tablename__ = "audios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))  # em backend/uploads
    format: Mapped[str] = mapped_column(String(20), default="wav_pcm")
    bits_per_sample: Mapped[int] = mapped_column(Integer)
    sample_rate_hz: Mapped[int] = mapped_column(Integer)
    channels: Mapped[int] = mapped_column(Integer)
    num_samples: Mapped[int] = mapped_column(Integer)  # por canal
    size_bytes: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now)

    # Um áudio tem várias análises; apagar o áudio apaga as análises dele.
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="audio", cascade="all, delete-orphan")

    @property
    def duration_s(self):
        """Calculada, não armazenada: duração = amostras / taxa."""
        return self.num_samples / self.sample_rate_hz

    def __repr__(self):
        return f"<Audio id={self.id} filename={self.filename!r}>"


class Analysis(Base):
    """Resultado de uma análise espectral (RF003), consultado pelo histórico."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audio_id: Mapped[int] = mapped_column(
        ForeignKey("audios.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True)

    # Parâmetros (RF002)
    block_size: Mapped[int] = mapped_column(Integer)
    window: Mapped[str] = mapped_column(String(20))

    # Resultado (RF003)
    blocks_used: Mapped[int] = mapped_column(Integer)
    magnitudes: Mapped[list] = mapped_column(JSON)  # block_size/2 + 1 valores
    peak_bin: Mapped[int] = mapped_column(Integer)
    peak_frequency_hz: Mapped[float] = mapped_column(Float)
    peak_magnitude: Mapped[float] = mapped_column(Float)
    warnings: Mapped[list] = mapped_column(JSON, default=list)

    audio: Mapped[Audio] = relationship(back_populates="analyses")

    @property
    def freq_resolution_hz(self):
        """Δf = fs / N (calculada a partir do áudio e do bloco)."""
        return self.audio.sample_rate_hz / self.block_size

    @property
    def frequencies_hz(self):
        """f[k] = k · fs / N, para k = 0 … N/2 (não precisa ser salva)."""
        df = self.freq_resolution_hz
        return [k * df for k in range(len(self.magnitudes))]

    def __repr__(self):
        return f"<Analysis id={self.id} audio_id={self.audio_id}>"
