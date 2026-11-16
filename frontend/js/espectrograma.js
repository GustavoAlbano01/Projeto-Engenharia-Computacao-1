/*
 * RF006 (desejável) - Espectrograma na INT02 (T29).
 *
 * Só gera a imagem quando o usuário pede: é o cálculo mais pesado do
 * sistema (até 1000 FFTs), então não roda toda vez que a tela abre.
 */

const botaoEspectrograma = document.getElementById("ver-espectrograma");
const imagemEspectrograma = document.getElementById("espectrograma");
const statusEspectrograma = document.getElementById("status-espectrograma");

/* Mensagem própria do cartão: a caixa #mensagem do topo pode estar
 * mostrando o aviso de bloco ajustado, que não deve ser apagado. */
function mostrarStatusEspectrograma(texto) {
  statusEspectrograma.textContent = texto;
  statusEspectrograma.hidden = false;
}

botaoEspectrograma.addEventListener("click", async () => {
  const id = lerIdDoEndereco();              // função do resultado.js
  if (id === null) return;

  botaoEspectrograma.disabled = true;
  mostrarStatusEspectrograma("Gerando o espectrograma...");
  try {
    const png = await buscarEspectrograma(id);     // Blob (image/png)
    imagemEspectrograma.src = URL.createObjectURL(png);
    imagemEspectrograma.hidden = false;
    statusEspectrograma.hidden = true;
    botaoEspectrograma.hidden = true;        // a imagem já está na tela
  } catch (erro) {
    mostrarStatusEspectrograma(erro.message);
    botaoEspectrograma.disabled = false;     // permite tentar de novo
  }
});