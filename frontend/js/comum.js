/*
 * Funções usadas por todas as telas (T22 - NF001, NF002).
 */

/* Rótulos em português para os valores do contrato (NF001). */
const NOMES_JANELA = {
  rectangular: "Retangular",
  hanning: "Hanning",
  hamming: "Hamming",
};

/* Mostra uma mensagem na caixa #mensagem da tela.
 * tipo: "erro" | "aviso" | "sucesso"
 */
function mostrarMensagem(texto, tipo = "erro") {
  const caixa = document.getElementById("mensagem");
  caixa.textContent = texto;          // textContent: nunca interpreta HTML
  caixa.className = `mensagem mensagem-${tipo}`;
  caixa.hidden = false;
}

function esconderMensagem() {
  document.getElementById("mensagem").hidden = true;
}

/* 2026-09-24T14:32:10Z -> 24/09/2026 11:32 (horário local) */
function formatarData(iso) {
  return new Date(iso).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

/* 440.123 -> "440,12 Hz" */
function formatarHz(valor) {
  return valor.toLocaleString("pt-BR", { maximumFractionDigits: 2 }) + " Hz";
}