/*
 * INT02 - Tela de resultado (T24 - RF004, T25 - RF005).
 *
 * Fluxo:
 *   1. lê o id da análise no endereço (resultado.html?id=N)
 *   2. busca a análise (GET /api/analyses/{id})
 *   3. mostra o resumo, os avisos e o gráfico magnitude x frequência
 *   4. interação: leitura sob o cursor, zoom e restaurar (RF005)
 */

const PISO_DB = -120;           // magnitudes muito pequenas param em -120 dB
const COR_LINHA = "#1f3864";    // mesma cor do cabeçalho (--azul)
const COR_PICO = "#c2611f";
const COR_GUIA = "#6b6b6b";     // linha-guia do cursor (--cinza)

let analise = null;             // análise carregada (para trocar a escala)
let escalaAtual = "linear";

/* ---------- 1. Id da análise ---------- */
function lerIdDoEndereco() {
  const id = Number(new URLSearchParams(window.location.search).get("id"));
  return Number.isInteger(id) && id > 0 ? id : null;
}

/* ---------- 2. Busca na API ---------- */
async function carregar() {
  const id = lerIdDoEndereco();
  if (id === null) {
    mostrarMensagem("Nenhuma análise foi indicada. Faça uma nova análise " +
                    "ou abra uma pelo histórico.");
    return;
  }

  mostrarMensagem("Carregando a análise...", "aviso");
  try {
    analise = await buscarAnalise(id);
  } catch (erro) {
    mostrarMensagem(erro.message);
    return;
  }

  esconderMensagem();
  mostrarResumo(analise);
  mostrarAvisos(analise.warnings);
  document.getElementById("cartao-grafico").hidden = false;
  desenharGrafico(analise, escalaAtual);
  ligarInteracao();
}

/* ---------- 3a. Resumo ---------- */
function taxaDeAmostragem(a) {
  // fs = Δf · N (o contrato não repete a taxa dentro da análise)
  return Math.round(a.freq_resolution_hz * a.params.block_size);
}

function mostrarResumo(a) {
  const preencher = (id, texto) => {
    document.getElementById(id).textContent = texto;   // nunca innerHTML
  };
  preencher("res-arquivo", a.audio.filename);
  preencher("res-data", formatarData(a.created_at));
  preencher("res-taxa", taxaDeAmostragem(a).toLocaleString("pt-BR") + " Hz");
  preencher("res-bloco", a.params.block_size.toLocaleString("pt-BR") + " amostras");
  preencher("res-janela", NOMES_JANELA[a.params.window] || a.params.window);
  preencher("res-blocos", String(a.blocks_used));
  preencher("res-resolucao", formatarHz(a.freq_resolution_hz));
  preencher("res-pico", formatarHz(a.peak.frequency_hz) + " (magnitude " +
    formatarMagnitude(a.peak.magnitude, "linear") + ")");
  document.getElementById("cartao-resumo").hidden = false;
}

/* Avisos não fatais, ex.: bloco ajustado (fluxo alternativo do RF002). */
function mostrarAvisos(avisos) {
  if (avisos && avisos.length > 0) {
    mostrarMensagem(avisos.map((aviso) => aviso.message).join(" "), "aviso");
  }
}

/* ---------- 3b. Gráfico (RF004) ---------- */
function paraDecibeis(m) {
  // 20·log10(m), como o contrato indica; o piso evita log10(0) = -infinito
  return Math.max(20 * Math.log10(m), PISO_DB);
}

/* 0.48504 -> "0,485" (linear) | -6.28 -> "-6,3 dB" (dB) */
function formatarMagnitude(valor, escala) {
  if (escala === "db") {
    return valor.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " dB";
  }
  return valor.toLocaleString("pt-BR", { maximumFractionDigits: 4 });
}

/* Última frequência do vetor = fs/2 (frequência de Nyquist). */
function nyquist(a) {
  return a.frequencies_hz[a.frequencies_hz.length - 1];
}

function desenharGrafico(a, escala) {
  const emDb = escala === "db";
  const y = emDb ? a.magnitudes.map(paraDecibeis) : a.magnitudes;
  const yPico = emDb ? paraDecibeis(a.peak.magnitude) : a.peak.magnitude;

  const espectro = {
    x: a.frequencies_hz,
    y: y,
    type: "scatter",
    mode: "lines",
    name: "Espectro",
    line: { color: COR_LINHA, width: 1.5 },
    hoverinfo: "none",          // a leitura aparece no painel #leitura (T25)
  };
  const pico = {
    x: [a.peak.frequency_hz],
    y: [yPico],
    type: "scatter",
    mode: "markers",
    name: "Pico",
    marker: { color: COR_PICO, size: 10 },
    hoverinfo: "none",
  };

  const layout = {
    separators: ",.",                       // 430,66 (vírgula decimal)
    margin: { l: 70, r: 20, t: 20, b: 60 },
    hovermode: "x",              // lê o ponto mais próximo na horizontal
    dragmode: "zoom",            // arrastar = ampliar a região (RF005)
    showlegend: false,
    xaxis: {
      title: "Frequência (Hz)",
      range: [0, nyquist(a)],
      showspikes: true,          // linha-guia vertical sob o cursor
      spikemode: "across",
      spikethickness: 1,
      spikedash: "dot",
      spikecolor: COR_GUIA,
    },
    yaxis: { title: emDb ? "Magnitude (dB)" : "Magnitude" },
  };

  const config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["select2d", "lasso2d"],
  };

  // react redesenha no mesmo lugar (usado também ao trocar a escala)
  Plotly.react("grafico", [espectro, pico], layout, config);
  marcarVisualizacaoOriginal();
}

/* ---------- 4. Interação (RF005 - T25) ---------- */
const grafico = document.getElementById("grafico");
const leitura = document.getElementById("leitura");
const botaoRestaurar = document.getElementById("restaurar");
const faixa = document.getElementById("faixa");

/* Liga os eventos do Plotly uma única vez (react não os remove). */
function ligarInteracao() {
  // Leitura sob o cursor: frequência e magnitude do ponto do espectro.
  grafico.on("plotly_hover", (evento) => {
    const ponto = evento.points.find((p) => p.curveNumber === 0);
    if (!ponto) return;
    leitura.textContent = `Cursor: ${formatarHz(ponto.x)} · magnitude ` +
      formatarMagnitude(ponto.y, escalaAtual);
  });
  grafico.on("plotly_unhover", () => {
    leitura.textContent = "Passe o mouse sobre o gráfico.";
  });

  // Zoom: o Plotly avisa a nova faixa dos eixos em plotly_relayout.
  grafico.on("plotly_relayout", (mudanca) => {
    if ("xaxis.range[0]" in mudanca) {
      marcarZoom(mudanca["xaxis.range[0]"], mudanca["xaxis.range[1]"]);
    } else if ("xaxis.autorange" in mudanca || "yaxis.autorange" in mudanca) {
      marcarVisualizacaoOriginal();      // duplo clique no gráfico
    } else if ("yaxis.range[0]" in mudanca) {
      botaoRestaurar.disabled = false;   // zoom só no eixo vertical
    }
  });
}

function marcarZoom(inicio, fim) {
  const de = Math.max(inicio, 0);
  const ate = Math.min(fim, nyquist(analise));
  faixa.textContent = `Ampliado: de ${formatarHz(de)} até ${formatarHz(ate)}.`;
  botaoRestaurar.disabled = false;
}

function marcarVisualizacaoOriginal() {
  faixa.textContent = "Exibindo de 0 Hz até a frequência de Nyquist " +
    `(${formatarHz(nyquist(analise))}).`;
  botaoRestaurar.disabled = true;
}

/* Restaurar: volta ao eixo X completo (0 até Nyquist) e ao Y automático. */
botaoRestaurar.addEventListener("click", () => {
  Plotly.relayout(grafico, {
    "xaxis.range": [0, nyquist(analise)],
    "yaxis.autorange": true,
  });
  marcarVisualizacaoOriginal();
});

/* Trocar a escala redesenha o gráfico e volta à visualização original. */
document.getElementById("escala").addEventListener("change", (evento) => {
  escalaAtual = evento.target.value;
  if (analise) desenharGrafico(analise, escalaAtual);
});

carregar();