-- Analisador Espectral de Áudio (AEA) - esquema do banco SQLite
-- Gerado a partir dos modelos SQLAlchemy (backend/app/models.py).
-- Uso: sqlite3 aea.db < schema.sql

PRAGMA foreign_keys = ON;

CREATE TABLE audios (
	id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	stored_path VARCHAR(500) NOT NULL, 
	format VARCHAR(20) NOT NULL, 
	bits_per_sample INTEGER NOT NULL, 
	sample_rate_hz INTEGER NOT NULL, 
	channels INTEGER NOT NULL, 
	num_samples INTEGER NOT NULL, 
	size_bytes INTEGER NOT NULL, 
	uploaded_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE analyses (
	id INTEGER NOT NULL, 
	audio_id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	block_size INTEGER NOT NULL, 
	window VARCHAR(20) NOT NULL, 
	blocks_used INTEGER NOT NULL, 
	magnitudes JSON NOT NULL, 
	peak_bin INTEGER NOT NULL, 
	peak_frequency_hz FLOAT NOT NULL, 
	peak_magnitude FLOAT NOT NULL, 
	warnings JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(audio_id) REFERENCES audios (id) ON DELETE CASCADE
);

CREATE INDEX ix_analyses_audio_id ON analyses (audio_id);
CREATE INDEX ix_analyses_created_at ON analyses (created_at);

