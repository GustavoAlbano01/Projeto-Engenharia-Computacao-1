# T31 – Teste ponta a ponta offline

Roteiro para simular a demonstração do Analisador Espectral de Áudio (AEA)
em uma única máquina, **sem internet** (NF005, NF011), passando por todos
os requisitos funcionais (RF001 a RF010).

O roteiro tem **duas colunas de resultado**:

| Coluna | Execução | Onde |
|---|---|---|
| **Auto** | Automatizada (script com navegador real), em 15/11/2026, commit `67f6fba` | Linux, 2 núcleos, 7 GB RAM, Python 3.13, NumPy 2.5.3, Chromium 153 |
| **Demo** | Manual, pela dupla (Eduardo Peron e Gustavo Albano Nunes), em 17/11/2026, commit `df8267c` (sistema = `67f6fba`) | Notebook Dell, Windows 11 Home 64 bits, 8 GB RAM, Python 3.14.10, Microsoft Edge 157.0.4341.42 |

Legenda: **OK** = igual ao esperado · **FALHA** = diferente (descrever em "Problemas encontrados").

> **Por que duas execuções?** A automatizada roda todos os casos do mesmo jeito,
> sempre, e registra os valores exatos. Mas o NF011 é sobre **o notebook da
> demonstração**: só a execução manual nele, com a rede desligada de verdade,
> prova que a apresentação vai funcionar.

---

## 1. Preparação (com internet)

| # | Ação | Esperado | Auto | Demo |
|---|---|---|---|---|
| P1 | `git checkout main` e `git pull` | `main` atualizada | OK | OK |
| P2 | `pip install -r backend/requirements.txt` | Nada novo para instalar, ou instalação sem erro | OK | OK |
| P3 | `python -m pytest -q` | Todos os testes passam (Auto: **184 passed**; Demo: **184 passed**) | OK | OK |
| P4 | `python backend/tools/gerar_sinais.py` | Pasta `sinais_teste/` com os WAV de teste | OK | OK |
| P5 | `python backend/tools/gerar_sinais.py --saida sinais_teste/curto --taxas 8000 --duracao 0.3` | WAV de 0,3 s (2400 amostras) | OK | OK |
| P6 | `python backend/tools/gerar_sinais.py --saida sinais_teste/muito_curto --taxas 8000 --duracao 0.01` | WAV de 0,01 s (80 amostras) | OK | OK |

## 2. Desligar a internet

| # | Ação | Esperado | Auto | Demo |
|---|---|---|---|---|
| P7 | Desligar o Wi-Fi e desconectar o cabo de rede | Ícone de rede sem conexão | (1) | OK |
| P8 | Abrir `https://www.google.com` no navegador | Página **não** abre (confirma que está offline) | OK | OK |
| P9 | `cd backend` e `python run.py` | `Running on http://127.0.0.1:5000`, sem erros | OK | OK |
| P10 | Abrir `http://localhost:5000/`, apertar `F12` → aba **Rede** (Network) → marcar **Preservar log** | Tela inicial (INT01) e a lista de requisições aberta | OK | OK |

> Deixe a aba **Rede** aberta durante todo o teste: ela é usada no CT15.

---

## 3. Casos de teste

### Envio e parâmetros (INT01)

| # | Requisito | Ação | Esperado | Auto | Demo |
|---|---|---|---|---|---|
| CT01 | RF001 | Escolher `sinais_teste/tom_440hz_44100.wav` | Mensagem verde "Arquivo válido…"; metadados: 3 s, 44.100 Hz, 1 (mono); botão **Analisar** habilitado | OK | OK |
| CT02 | RF001, NF002 | Escolher um arquivo que não seja `.wav` (filtro "Todos os arquivos") | "Formato não suportado. Selecione um arquivo .wav."; **nenhum** `POST /api/audios` na aba Rede | OK | OK |
| CT03 | RF001, NF002 | Escolher um texto renomeado para `.wav` (criar com `Set-Content sinais_teste\falso.wav "nao e wav"`) | "O arquivo está corrompido ou não é um WAV válido."; botão Analisar desabilitado | OK | OK |

### Análise e resultado (INT02)

| # | Requisito | Ação | Esperado | Auto | Demo |
|---|---|---|---|---|---|
| CT04 | RF002, RF003 | `tom_440hz_44100.wav`, bloco **1024**, **Hanning** → Analisar | Abre `resultado.html?id=N`; pico em **430,66 Hz**, magnitude ≈ **0,48** | OK | OK |
| CT05 | RF003, RF004, RF010 | `dois_tons_440_1000hz_44100.wav`, 1024, Hanning | Gráfico com **dois picos**, perto de 440 Hz e de 1000 Hz | OK | OK |
| CT06 | RF004 | Trocar a escala para **Decibéis (dB)** e voltar para **Linear** | O gráfico muda de escala sem recarregar a página | OK | OK |
| CT07 | RF005 | Passar o mouse; arrastar para dar zoom; clicar em **Restaurar visualização**; dar duplo clique | Leitura de frequência e magnitude sob o cursor; faixa "Ampliado: de … até …"; volta para 0 Hz até Nyquist | OK | OK |
| CT08 | NF001 | Passar o mouse nos botões da barra do gráfico | Dicas em português ("Mover", "Restaurar eixos", …); aviso "Duplo clique para reverter zoom" | OK | OK |
| CT09 | RF006 | Clicar em **Ver espectrograma** | Imagem com linhas em 440 e 1000 Hz; eixos com vírgula decimal (0,5) e ponto de milhar (20.000) | OK | OK |
| CT10 | RF002 (bloco ajustado) | `sinais_teste/curto/tom_1000hz_8000.wav`, bloco **4096** | Aviso amarelo "O bloco solicitado (4096) é maior que o áudio. Foi usado 2048."; o aviso **continua** depois de ver o espectrograma | OK | OK |
| CT11 | RF002 (áudio curto), NF002 | `sinais_teste/muito_curto/tom_1000hz_8000.wav` → Analisar | Envio aceito; análise recusada com "O áudio é curto demais para análise (mínimo de 512 amostras)."; botão Analisar volta a ficar habilitado | OK | OK |

### Histórico (INT03)

| # | Requisito | Ação | Esperado | Auto | Demo |
|---|---|---|---|---|---|
| CT12 | RF007 | Abrir **Histórico** | Análises dos casos anteriores, **mais recente primeiro**; data, arquivo, bloco, janela e pico | OK | OK |
| CT13 | RF008 | Clicar em **Abrir** na análise do CT04 | Mesmo resultado do CT04; na aba Rede, só `GET /api/analyses/N` (**nenhum** `POST`: sem reprocessar) | OK | OK |
| CT14 | RF009 | **Excluir** uma análise → **Cancelar**; depois **Excluir** → **OK** | Cancelar não muda nada; OK remove a linha e mostra "Análise excluída do histórico." | OK | OK |

### Requisitos não funcionais

| # | Requisito | Ação | Esperado | Auto | Demo |
|---|---|---|---|---|---|
| CT15 | NF005, NF011 | Na aba **Rede**, conferir todas as requisições feitas até aqui | Todas para `localhost:5000`; nenhuma para outro endereço; nenhum recurso com falha (exceto `favicon.ico`) | OK | OK (2) |
| CT16 | NF007 | Parar o servidor (`Ctrl + C`), rodar `python run.py` de novo e abrir o Histórico | As análises continuam lá | OK | OK |
| CT17 | NF002 | Abrir uma análise **sem** gerar o espectrograma; parar o servidor; clicar em **Ver espectrograma** | "Não foi possível conectar ao servidor. Verifique se o backend está rodando (python run.py)." | OK | OK |
| CT18 | NF004 | Na raiz, com o servidor parado: `python backend/tools/medir_tempo.py` | "NF004 atendido" (Auto: pior caso **0,238 s**; Demo: **1,040 s**) | OK | OK |
| CT19 | NF001 | Percorrer as três telas procurando textos em inglês ou jargão | Nenhum texto em inglês visível para o usuário | OK | OK |

---

## 4. Resumo

| Execução | Casos | OK | FALHA |
|---|---|---|---|
| Auto | 19 (+ 10 de preparação) | **19** | **0** |
| Demo | 19 (+ 10 de preparação) | **19** | **0** |

(1) Na execução automatizada, a "internet desligada" foi simulada: o navegador
bloqueou e registrou **todo** acesso que não fosse para `127.0.0.1:5055`. O P8
confirma o bloqueio (o google.com não abriu). Na execução Demo, o Wi-Fi foi
desligado de verdade.

(2) Na execução Demo, o filtro `-domain:localhost` mostrou 4 imagens
`data:image/webp`. Não são acessos à rede: a imagem vem embutida no próprio
endereço (0 B transferidos). Detalhes na seção 4.2.

## 4.1 Evidências da execução automatizada

Valores obtidos em cada caso:

| # | Resultado | Valor obtido |
|---|---|---|
| P8 | OK | google.com não abre (acessos externos bloqueados): https://www.google.com/ |
| P10 | OK | INT01 abriu em localhost:5000 |
| CT01 | OK | Nome: tom_440hz_44100.wav · Duração: 3 s · Taxa: 44.100 Hz · Canais: 1 (mono) |
| CT02 | OK | Formato não suportado. Selecione um arquivo .wav. / POST enviados: 0 |
| CT03 | OK | O arquivo está corrompido ou não é um WAV válido. |
| CT04 | OK | id 1: 430,66 Hz (magnitude 0,485) |
| CT05 | OK | magnitude em 440 Hz = 0,388; em 1000 Hz = 0,388; em 700 Hz (entre os tons) = 0,00046 |
| CT06 | OK | eixo Y: "Magnitude (dB)" -> "Magnitude", sem novas requisições |
| CT07 | OK | "Cursor: 2.411,72 Hz · magnitude 0" / "Ampliado: de 554,02 Hz até 6.592,84 Hz." / "Exibindo de 0 Hz até a frequência de Nyquist (22.050 Hz)." |
| CT08 | OK | botões: Fazer download do gráfico como imagem (png), Zoom, Mover, Ampliar zoom, Reduzir zoom, Escala automática, Restaurar eixos / aviso: "Duplo clique para reverter zoom" |
| CT09 | OK | imagem 1000 × 450 px (conferida visualmente: linhas em 440 e 1000 Hz, eixos 0,5 e 20.000) |
| CT10 | OK | "O bloco solicitado (4096) é maior que o áudio. Foi usado 2048." (continua após o espectrograma: true) |
| CT11 | OK | O áudio é curto demais para análise (mínimo de 512 amostras). |
| CT12 | OK | 3 linhas, ids 3, 2, 1 (mais recente primeiro) |
| CT13 | OK | pico igual ao CT04; requisições à API: GET /api/analyses/1 |
| CT14 | OK | cancelar: 3 linhas; OK: 2 linhas, "Análise excluída do histórico." |
| CT15 | OK | 102 requisições, todas para 127.0.0.1:5055; externas: 0; arquivos com falha: 0 |
| CT16 | OK | ids antes: 2,1; depois de reiniciar: 2,1 |
| CT17 | OK | Não foi possível conectar ao servidor. Verifique se o backend está rodando (python run.py). |
| CT18 | OK | NF004 atendido: pior caso 0,238 s (limite: 2 s) |
| CT19 | OK | nenhum texto em inglês nas três telas |
| — | OK | Nenhum erro de JavaScript em toda a execução |

Imagem do espectrograma do CT09: `docs/testes/T31_CT09_espectrograma.png`.

## 4.2 Evidências da execução Demo

Valores observados no notebook da demonstração:

| # | Resultado | Valor obtido |
|---|---|---|
| P3 | OK | 184 passed |
| CT04 | OK | 430,66 Hz (magnitude 0,485), igual à Auto |
| CT14 | OK | Cancelar: 3 linhas; OK: 2 linhas, "Análise excluída do histórico." |
| CT15 | OK | 98 solicitações; externas: 0. Apareceram 4 imagens `data:image/webp` (0 B, da memória): são embutidas no próprio endereço e não acessam a rede. Com o filtro `-domain:localhost -scheme:data`: 0 |
| CT16 | OK | As 2 análises continuaram no histórico depois de reiniciar o servidor |
| CT18 | OK | NF004 atendido: pior caso 1,040 s (4096, Hamming; média 0,871 s). Cerca de 4,4 vezes mais lento que a Auto, ainda dentro do limite de 2 s |

Prints: `docs/testes/T31_CT09_demo.png`, `docs/testes/T31_CT12_demo.png`, `docs/testes/T31_CT15_demo.png`.

## 5. Problemas encontrados

| # | Execução | Caso | O que aconteceu | Correção (cartão/PR) |
|---|---|---|---|---|
| 1 | Auto | CT15 | Na primeira rodada, o CT15 acusou 1 acesso externo. Era o próprio teste do P8 (abrir o google.com), registrado no mesmo navegador. **Não era falha do sistema**: o contador passou a ser zerado depois do P8, e a nova rodada deu 0 acessos externos | Ajuste no script de teste (sem mudança no sistema) |

Na execução Demo não foram encontrados problemas.

## 6. Conclusão

**Execução automatizada:** 19 de 19 casos OK, nenhum acesso fora de `localhost` e nenhum erro de JavaScript.

**Execução Demo:** 19 de 19 casos OK no notebook da demonstração, com o Wi-Fi desligado.

(X) O sistema funcionou integralmente offline, em uma única máquina (NF005, NF011), e está pronto para a demonstração.

( ) Foram encontrados problemas; ver seção 5.
