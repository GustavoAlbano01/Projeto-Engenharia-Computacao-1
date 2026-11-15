/*
 * INT03 - Tela de histórico (T27 - RF007, RF008).
 *
 * Fluxo:
 *   1. busca a lista (GET /api/analyses), já ordenada da mais recente
 *   2. lista vazia -> avisa; senão monta uma linha por análise
 *   3. "Abrir" leva a resultado.html?id=N (RF008, sem reprocessar)
 */

const tabela = document.getElementById("tabela");
const linhas = document.getElementById("linhas");
const avisoVazio = document.getElementById("vazio");

async function carregarHistorico() {
  mostrarMensagem("Carregando o histórico...", "aviso");
  let lista;
  try {
    lista = await listarAnalises();
  } catch (erro) {
    mostrarMensagem(erro.message);
    return;
  }
  esconderMensagem();
  mostrarLista(lista);
}

function mostrarLista(lista) {
  linhas.replaceChildren();              // apaga as linhas anteriores

  if (lista.length === 0) {              // fluxo alternativo do RF007
    tabela.hidden = true;
    avisoVazio.hidden = false;
    return;
  }

  for (const analise of lista) {
    linhas.appendChild(criarLinha(analise));
  }
  avisoVazio.hidden = true;
  tabela.hidden = false;
}

/* Uma linha <tr> da tabela. Usa textContent: o nome do arquivo vem do
 * usuário e nunca deve ser interpretado como HTML. */
function criarLinha(analise) {
  const tr = document.createElement("tr");

  const celulas = [
    formatarData(analise.created_at),
    analise.audio.filename,
    analise.params.block_size.toLocaleString("pt-BR"),
    NOMES_JANELA[analise.params.window] || analise.params.window,
    formatarHz(analise.peak.frequency_hz),
  ];
  for (const texto of celulas) {
    const td = document.createElement("td");
    td.textContent = texto;
    tr.appendChild(td);
  }

  // Ações: reabrir a análise (RF008).
  const acoes = document.createElement("td");
  const abrir = document.createElement("a");
  abrir.href = `resultado.html?id=${analise.id}`;
  abrir.textContent = "Abrir";
  acoes.appendChild(abrir);

  // Excluir, com confirmação (RF009 - T28)
  const excluir = document.createElement("button");
  excluir.type = "button";
  excluir.className = "perigo pequeno";
  excluir.textContent = "Excluir";
  excluir.addEventListener("click", () => confirmarExclusao(analise, excluir));
  acoes.appendChild(excluir);

  tr.appendChild(acoes);

  return tr;
}

/* RF009 - pede confirmação e exclui a análise (T28). */
async function confirmarExclusao(analise, botao) {
  const quando = formatarData(analise.created_at);
  const certeza = window.confirm(
    `Excluir a análise de "${analise.audio.filename}" (${quando})?\n\n` +
    "Esta ação não pode ser desfeita.");
  if (!certeza) return;                      // usuário clicou em Cancelar

  botao.disabled = true;                     // evita clique duplo
  try {
    await excluirAnalise(analise.id);        // DELETE /api/analyses/{id}
  } catch (erro) {
    await carregarHistorico();               // a lista pode ter mudado
    mostrarMensagem(erro.message);
    return;
  }
  await carregarHistorico();                 // redesenha sem a linha
  mostrarMensagem("Análise excluída do histórico.", "sucesso");
}

carregarHistorico();