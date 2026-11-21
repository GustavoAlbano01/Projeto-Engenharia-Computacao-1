# Benchmark DFT × FFT (T34) - valores medidos

Gerado por `python backend/tools/benchmark_dft_fft.py`.

## Ambiente
- Data: 20/11/2026
- Processador: Intel64 Family 6 Model 165 Stepping 3, GenuineIntel
- Sistema: Windows 11
- Python 3.12.0, NumPy 2.5.3

## Ordem de crescimento (inclinação em log-log, t ∝ N^a)
- DFT direta: a = 1,93 (teórico: 2), N de 1024 a 8192.
- FFT própria: a = 1,04 (teórico para N·log₂N nesses N: 1,11), N de 2048 a 65536.

## Ganho da FFT
- Com N = 8192: DFT 2257,2 ms, FFT 1,189 ms, FFT 1898 vezes mais rápida (razão teórica N/log₂N = 630).
