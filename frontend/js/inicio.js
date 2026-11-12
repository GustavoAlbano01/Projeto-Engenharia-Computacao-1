/*
 * INT01 - Tela inicial (T23 - RF001, RF002).
 *
 * Fluxo:
 *   1. o usuário escolhe o arquivo -> envia na hora (POST /api/audios)
 *   2. mostra os metadados e habilita "Analisar"
 *   3. "Analisar" -> POST /api/analyses -> abre resultado.html?id=N
 */

const LIMITE_BYTES = 60 * 1024 * 1024;   // 60 MB (NF006), igual ao backend

const campoArquivo = document.getElementById("arquivo");
const campoBloco = document.getElementById("bloco");
const campoJanela = document.getElementById("janela");
const botaoAnalisar = document.getElementById("analisar");

let audioId = null;   // id do áudio já enviado e validado pelo backend

/* ---------- 1. Envio do arquivo (RF001) ---------- */
campoArquivo.addEventListener("change", async () => {
  // Um arquivo novo invalida o anterior.
  audioId = null;
  botaoAnalisar.disabled = true;
  document.getElementById("metadados").hidden = true;
  esconderMensagem();

  const arquivo = campoArquivo.files[0];
  if (!arquivo) return;                      // o usuário cancelou a escolha

  // Validação rápida antes de enviar (o backend valida de novo).
  if (!arquivo.name.toLowerCase().endsWith(".wav")) {
    mostrarMensagem("Formato não suportado. Selecione um arquivo .wav.");
    return;
  }
  if (arquivo.size > LIMITE_BYTES) {
    mostrarMensagem("O arquivo tem mais de 60 MB. Selecione um arquivo menor.");
    return;
  }

  campoArquivo.disabled = true;
  mostrarMensagem("Enviando e validando o arquivo...", "aviso");
  try {
    const audio = await enviarAudio(arquivo);
    audioId = audio.id;
    mostrarMetadados(audio);
    botaoAnalisar.disabled = false;
    mostrarMensagem("Arquivo válido. Escolha os parâmetros e clique em Analisar.",
                    "sucesso");
  } catch (erro) {
    mostrarMensagem(erro.message);
  } finally {
    campoArquivo.disabled = false;
  }
});

function mostrarMetadados(audio) {
  document.getElementById("meta-nome").textContent = audio.filename;
  document.getElementById("meta-duracao").textContent =
    audio.duration_s.toLocaleString("pt-BR", { maximumFractionDigits: 2 }) + " s";
  document.getElementById("meta-taxa").textContent =
    audio.sample_rate_hz.toLocaleString("pt-BR") + " Hz";
  document.getElementById("meta-canais").textContent =
    audio.channels === 1 ? "1 (mono)" : `${audio.channels} (estéreo)`;
  document.getElementById("metadados").hidden = false;
}