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

  // Ações: reabrir a análise (RF008). A exclusão (RF009) entra na T28.
  const acoes = document.createElement("td");
  const abrir = document.createElement("a");
  abrir.href = `resultado.html?id=${analise.id}`;
  abrir.textContent = "Abrir";
  acoes.appendChild(abrir);
  tr.appendChild(acoes);

  return tr;
}

carregarHistorico();