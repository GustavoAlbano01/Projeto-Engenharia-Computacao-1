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