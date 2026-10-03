# Contrato da API — Analisador Espectral de Áudio (AEA)

Versão do contrato: **v1** · Base URL: `http://localhost:5000/api` · Requisito: **NF009**

## 1. Convenções gerais

| Item | Convenção |
|---|---|
| Formato | JSON (`Content-Type: application/json; charset=utf-8`), exceto upload (`multipart/form-data`) e espectrograma (`image/png`) |
| Nomes de campos | `snake_case` (mesmo padrão do Python/PEP 8) |
| Unidades | Sempre no nome do campo: `_hz`, `_s`, `_bytes` |
| Datas | ISO 8601 em UTC, ex.: `"2026-09-24T14:32:10Z"` |
| IDs | Inteiros gerados pelo SQLite |
| Sucesso | O recurso é devolvido direto, sem envelope |
| Erro | Sempre no envelope `{"error": {...}}` (seção 5) |
| Idioma | `code` em inglês (para o código tratar); `message` em português (para exibir — NF001/NF002) |

### Valores permitidos (enums)

- `window`: `"rectangular"` | `"hanning"` | `"hamming"`
- `block_size`: `512` | `1024` | `2048` | `4096`
- Áudio aceito: WAV PCM 16 bits, mono ou estéreo, até 60 MB

## 2. Tabela de rotas

| Método | Rota | Requisito | Sucesso | Descrição |
|---|---|---|---|---|
| POST | `/api/audios` | RF001 | 201 | Envia e valida um WAV; devolve metadados |
| POST | `/api/analyses` | RF002, RF003 | 201 | Calcula o espectro médio e salva a análise |
| GET | `/api/analyses` | RF007 | 200 | Lista o histórico (resumo, mais recente primeiro) |
| GET | `/api/analyses/{id}` | RF008 | 200 | Análise completa (com vetores) |
| DELETE | `/api/analyses/{id}` | RF009 | 204 | Exclui a análise (sem corpo) |
| GET | `/api/analyses/{id}/spectrogram` | RF006 (desejável) | 200 | Imagem PNG do espectrograma |

## 3. Áudio

### POST `/api/audios`

**Requisição:** `multipart/form-data` com o campo `file`.

**Resposta 201:**
```json
{
  "id": 7,
  "filename": "tom_440hz.wav",
  "format": "wav_pcm",
  "bits_per_sample": 16,
  "sample_rate_hz": 44100,
  "channels": 1,
  "num_samples": 132300,
  "duration_s": 3.0,
  "size_bytes": 264644,
  "uploaded_at": "2026-09-24T14:31:58Z"
}
```
- `num_samples`: amostras **por canal**. Logo `duration_s = num_samples / sample_rate_hz`.

**Erros possíveis:** `FILE_MISSING` (400), `INVALID_WAV` (400), `EMPTY_AUDIO` (400), `UNSUPPORTED_FORMAT` (415), `FILE_TOO_LARGE` (413).

## 4. Análise

### POST `/api/analyses`

**Requisição:**
```json
{ "audio_id": 7, "block_size": 1024, "window": "hanning" }
```

**Resposta 201** (vetores encurtados aqui; exemplo completo em `mocks/analysis_create_201.json`):
```json
{
  "id": 12,
  "audio": { "id": 7, "filename": "tom_440hz.wav" },
  "created_at": "2026-09-24T14:32:10Z",
  "params": { "block_size": 1024, "window": "hanning" },
  "blocks_used": 256,
  "freq_resolution_hz": 43.0664,
  "frequencies_hz": [0.0, 43.07, 86.13, "..."],
  "magnitudes": [0.000123, 0.000098, 0.000101, "..."],
  "peak": { "bin": 10, "frequency_hz": 430.66, "magnitude": 0.485044 },
  "warnings": []
}
```

Regras dos campos:
- `frequencies_hz[k] = k · sample_rate_hz / block_size`, para `k = 0 … block_size/2` → os dois vetores têm `block_size/2 + 1` posições e **sempre o mesmo tamanho**.
- `magnitudes`: amplitude linear normalizada (uma senoide de amplitude A em fundo de escala aparece com valor ≈ A). Conversão para dB fica a cargo do frontend: `20·log10(m)`.
- `blocks_used`: nº de blocos igualmente espaçados usados na média (máximo 256).
- `peak`: maior magnitude **ignorando o bin 0 (componente DC)**.
- Estéreo: os canais são convertidos para mono pela média antes da FFT.
- `warnings`: avisos não fatais. Ex.: bloco maior que o áudio (fluxo alternativo do RF002):
```json
"warnings": [
  {
    "code": "BLOCK_SIZE_ADJUSTED",
    "message": "O bloco solicitado (4096) é maior que o áudio. Foi usado 2048.",
    "details": { "requested": 4096, "used": 2048 }
  }
]
```

**Erros possíveis:** `INVALID_PARAMETER` (400), `AUDIO_TOO_SHORT` (400), `AUDIO_NOT_FOUND` (404), `INTERNAL_ERROR` (500).

### GET `/api/analyses` — histórico (resumo, sem vetores)

**Resposta 200:**
```json
[
  {
    "id": 12,
    "created_at": "2026-09-24T14:32:10Z",
    "audio": { "id": 7, "filename": "tom_440hz.wav" },
    "params": { "block_size": 1024, "window": "hanning" },
    "peak": { "frequency_hz": 430.66, "magnitude": 0.485044 }
  }
]
```
Histórico vazio → `[]` com status 200 (não é erro).

### GET `/api/analyses/{id}`
**200:** mesmo formato do POST `/api/analyses`. **404:** `ANALYSIS_NOT_FOUND`.

### DELETE `/api/analyses/{id}`
**204:** sem corpo. **404:** `ANALYSIS_NOT_FOUND`.

### GET `/api/analyses/{id}/spectrogram` (desejável)
**200:** `image/png`. **404:** `ANALYSIS_NOT_FOUND`.

## 5. Erros

Envelope único:
```json
{
  "error": {
    "code": "UNSUPPORTED_FORMAT",
    "message": "Formato não suportado. Envie um arquivo WAV PCM de 16 bits.",
    "details": { "received_extension": ".mp3" }
  }
}
```
`details` é opcional.

| `code` | HTTP | Quando ocorre |
|---|---|---|
| `FILE_MISSING` | 400 | Requisição de upload sem o campo `file` |
| `INVALID_WAV` | 400 | Cabeçalho RIFF/WAVE inválido ou arquivo corrompido |
| `EMPTY_AUDIO` | 400 | WAV sem amostras |
| `INVALID_PARAMETER` | 400 | `block_size`/`window` fora dos enums, JSON malformado ou campo faltando |
| `AUDIO_TOO_SHORT` | 400 | Áudio com menos amostras que o menor bloco (512) — fluxo alternativo do RF002 |
| `AUDIO_NOT_FOUND` | 404 | `audio_id` inexistente |
| `ANALYSIS_NOT_FOUND` | 404 | `id` de análise inexistente |
| `FILE_TOO_LARGE` | 413 | Upload acima de 60 MB |
| `UNSUPPORTED_FORMAT` | 415 | Não é WAV, ou WAV não PCM 16 bits |
| `INTERNAL_ERROR` | 500 | Exceção não prevista (inclui falha de gravação no banco) |
| `NOT_IMPLEMENTED` | 501 | Rota prevista mas ainda não implementada (espectrograma) |
| `HTTP_<status>` | 404/405 | Rota inexistente ou método HTTP errado (ex.: `HTTP_405`) |

Regra (NF003): nenhuma exceção pode derrubar o servidor; toda falha vira uma resposta neste formato.

## 6. Mocks para o frontend

| Arquivo | Simula |
|---|---|
| `backend/mocks/audio_upload_201.json` | POST `/api/audios` com sucesso |
| `backend/mocks/analysis_create_201.json` | POST `/api/analyses` — tom de 440 Hz, fs = 44,1 kHz, bloco 1024, Hanning (513 pontos) |
| `backend/mocks/analysis_block_adjusted_201_trecho.json` | Trecho com aviso de bloco ajustado |
| `backend/mocks/analyses_list_200.json` | GET `/api/analyses` |
| `backend/mocks/error_415.json` | Erro de formato não suportado |
