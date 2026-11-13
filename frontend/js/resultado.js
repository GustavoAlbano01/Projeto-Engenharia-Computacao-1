/*
 * INT02 - Tela de resultado: resumo e gráfico do espectro (T24 - RF004).
 *
 * Fluxo:
 *   1. lê o id da análise no endereço (resultado.html?id=N)
 *   2. busca a análise (GET /api/analyses/{id})
 *   3. mostra o resumo, os avisos e o gráfico magnitude x frequência
 */

const PISO_DB = -120;           // magnitudes muito pequenas param em -120 dB
const COR_LINHA = "#1f3864";    // mesma cor do cabeçalho (--azul)
const COR_PICO = "#c2611f";

let analise = null;             // análise carregada (para trocar a escala)

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
  desenharGrafico(analise, "linear");
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
    a.peak.magnitude.toLocaleString("pt-BR", { maximumFractionDigits: 4 }) + ")");
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

function desenharGrafico(a, escala) {
  const emDb = escala === "db";
  const y = emDb ? a.magnitudes.map(paraDecibeis) : a.magnitudes;
  const yPico = emDb ? paraDecibeis(a.peak.magnitude) : a.peak.magnitude;
  const formatoY = emDb ? "%{y:.1f} dB" : "%{y:.4f}";
  const nyquist = a.frequencies_hz[a.frequencies_hz.length - 1];

  const espectro = {
    x: a.frequencies_hz,
    y: y,
    type: "scatter",
    mode: "lines",
    name: "Espectro",
    line: { color: COR_LINHA, width: 1.5 },
    hovertemplate: `%{x:.2f} Hz<br>${formatoY}<extra></extra>`,
  };
  const pico = {
    x: [a.peak.frequency_hz],
    y: [yPico],
    type: "scatter",
    mode: "markers",
    name: "Pico",
    marker: { color: COR_PICO, size: 10 },
    hovertemplate: `Pico: %{x:.2f} Hz<br>${formatoY}<extra></extra>`,
  };

  const layout = {
    separators: ",.",                       // 430,66 (vírgula decimal)
    margin: { l: 70, r: 20, t: 20, b: 60 },
    hovermode: "closest",
    showlegend: false,
    xaxis: { title: "Frequência (Hz)", range: [0, nyquist] },
    yaxis: { title: emDb ? "Magnitude (dB)" : "Magnitude" },
  };

  const config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["select2d", "lasso2d"],
  };

  // react redesenha no mesmo lugar (usado também ao trocar a escala)
  Plotly.react("grafico", [espectro, pico], layout, config);
}

document.getElementById("escala").addEventListener("change", (evento) => {
  if (analise) desenharGrafico(analise, evento.target.value);
});

carregar();