/*
 * Chamadas à API do backend (T22 - NF009, NF010).
 *
 * Todas as funções devolvem uma Promise:
 *   - sucesso: o JSON do contrato (docs/CONTRATO_API.md);
 *   - falha:   lança um ErroApi com a mensagem em português (NF002).
 *
 * O frontend é servido pelo próprio Flask (mesma origem), então as rotas
 * começam direto com /api, sem http://localhost:5000.
 */

const API = "/api";

class ErroApi extends Error {
  constructor(mensagem, codigo, status, detalhes) {
    super(mensagem);
    this.codigo = codigo;       // ex.: "INVALID_WAV" (para o código decidir)
    this.status = status;       // ex.: 400
    this.detalhes = detalhes;   // campo "details" do contrato, se houver
  }
}

/* Faz a requisição e trata os três tipos de falha. */
async function requisitar(caminho, opcoes = {}) {
  // 1. Servidor fora do ar: o próprio fetch lança um erro.
  let resposta;
  try {
    resposta = await fetch(API + caminho, opcoes);
  } catch (e) {
    throw new ErroApi(
      "Não foi possível conectar ao servidor. Verifique se o backend está " +
        "rodando (python run.py).",
      "NETWORK_ERROR", 0);
  }

  // DELETE devolve 204, sem corpo: não há JSON para ler.
  if (resposta.status === 204) return null;

  // Lê o corpo como JSON (pode falhar se não for JSON).
  let corpo = null;
  try {
    corpo = await resposta.json();
  } catch (e) {
    // corpo vazio ou não-JSON: tratado logo abaixo
  }

  if (!resposta.ok) {
    // 2. Erro no formato do contrato: {"error": {"code", "message", "details"}}
    if (corpo && corpo.error) {
      const { code, message, details } = corpo.error;
      throw new ErroApi(message, code, resposta.status, details);
    }
    // 3. Erro fora do contrato.
    throw new ErroApi(
      `Erro inesperado do servidor (HTTP ${resposta.status}).`,
      "UNEXPECTED", resposta.status);
  }
  return corpo;
}

/* RF001 - POST /api/audios (multipart, campo "file") */
function enviarAudio(arquivo) {
  const formulario = new FormData();
  formulario.append("file", arquivo);
  return requisitar("/audios", { method: "POST", body: formulario });
}

/* RF002/RF003 - POST /api/analyses */
function criarAnalise(audioId, blockSize, window) {
  return requisitar("/analyses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      audio_id: audioId,
      block_size: blockSize,
      window: window,
    }),
  });
}

/* RF007 - GET /api/analyses */
function listarAnalises() {
  return requisitar("/analyses");
}

/* RF008 - GET /api/analyses/{id} */
function buscarAnalise(id) {
  return requisitar(`/analyses/${id}`);
}

/* RF009 - DELETE /api/analyses/{id} */
function excluirAnalise(id) {
  return requisitar(`/analyses/${id}`, { method: "DELETE" });
}