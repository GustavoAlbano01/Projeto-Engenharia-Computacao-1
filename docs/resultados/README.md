# Resultados de desempenho (T21 - NF004)

Gerados por `python backend/tools/medir_tempo.py` (3 repetições por combinação).

## Ambiente da medição
- Data: 08/11/2026
- Processador: AMD Ryzen 5 7600X, 6 núcleos, 4,70 GHz
- Memória RAM: 16 GB
- Sistema: Windows 11, 64 bits
- Python 3.14.8, NumPy 2.5.3

## Arquivos
- `tempo_resposta.csv`: POST /api/analyses no pior caso (WAV de 5 min,
  48 kHz, estéreo, 57,6 MB), para cada bloco e janela.
- `dft_fft.csv`: tempo de um bloco com a DFT direta (T15) e a FFT própria (T16).

## Conclusões
- NF004 atendido: pior caso de 0,371 s (bloco 4096), limite de 2 s.
- Upload + pior análise: 0,85 s.
- A janela não altera o tempo de forma significativa.
- Cerca de metade do tempo de resposta é a leitura do WAV (custo fixo).
- A vantagem da FFT sobre a DFT cresce com N: de 60× (N = 512) a 945× (N = 4096).
- As medições foram feitas em um desktop (Ryzen 5 7600X). Em máquinas mais
  lentas o tempo aumenta, mas a folga de 5,4× em relação ao limite do NF004
  indica que o requisito continua atendido em computadores comuns.


# Validação com sinais de referência (T32 - RF010, NF012)

Gerados por `python backend/tools/validar_picos.py`. Não dependem do
computador: os sinais são sintéticos e o resultado é sempre o mesmo.

## Método
- Tons puros de 440 Hz e 1000 Hz, amplitude 0,5, 3 s, gerados pelo T10.
- Taxas de 8000, 22050, 44100 e 48000 Hz.
- Janelas retangular, Hanning e Hamming; blocos de 512, 1024, 2048 e 4096.
- Caminho igual ao da API: WAV -> `read_wav` (T11) -> `analyze` (T20).
- Critério (NF012): |erro| <= fs/N (um bin).

## Arquivos
- `validacao_picos.csv`: as 96 combinações (2 tons × 4 taxas × 3 janelas × 4 blocos),
  com resolução, frequência detectada, erro em Hz, em % e em bins, e magnitude do pico.
- `tabela1_artigo.csv`: Tabela 1 do artigo (fs = 44,1 kHz, 24 linhas).

## Conclusões
- 96 de 96 casos dentro de um bin: NF012 atendido.
- O erro nunca passou de meio bin (pior caso: 0,453 bin), ou seja, o pico
  sempre caiu no bin mais próximo da frequência real.
- Maior erro relativo: 6,53 % (440 Hz, fs = 48 kHz, N = 512, Δf = 93,75 Hz).
  Com N = 4096 o erro relativo fica entre 0 % e 1,21 % (1000 Hz a 8 kHz
  cai exatamente sobre um bin).
- A janela não mudou a frequência detectada em nenhum caso; ela muda a
  magnitude do pico e o vazamento (ver `test_validacao_dsp.py`). Quem define o
  erro em frequência é a resolução Δf = fs/N.