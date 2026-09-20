# Decisões de projeto

| Data | Decisão | Motivo |
|---|---|---|
| 20/09/2026 | A FFT é implementada no próprio projeto (radix-2). O `numpy.fft` é usado apenas como referência nos testes. | A proposta prevê implementar a FFT; permite o benchmark DFT × FFT para o artigo. |
| 20/09/2026 | Apenas arquivos WAV PCM de 16 bits. MP3 fora do escopo. | Consistência entre a proposta e a interface; MP3 exigiria decodificador externo. |
| 20/09/2026 | Limite de upload de 60 MB. | 5 min a 48 kHz, 16 bits, estéreo ocupam cerca de 57,6 MB. |
| 20/09/2026 | O espectro é a média de até 256 blocos igualmente espaçados. | Manter o tempo de resposta de até 2 s (NF004). |
| Anterior | Software de uso pessoal e local, sem autenticação. | Poucos meses de prazo para o desenvolvimento. |
| Anterior | Persistência com histórico de análises em SQLite. | Exigência do professor de usar banco de dados. |
