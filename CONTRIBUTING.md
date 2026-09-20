# Como trabalhamos neste repositório

## Commits

Usamos mensagens curtas no formato `tipo(escopo): descrição`, em português, no imperativo ou no infinitivo, sem ponto final.

| Tipo | Quando usar |
|---|---|
| `feat` | nova funcionalidade |
| `fix` | correção de erro |
| `test` | testes |
| `docs` | documentação |
| `refactor` | mudança de código sem alterar o comportamento |
| `chore` | estrutura, configuração, dependências |

Exemplos:

```
feat(audio): ler cabeçalho e amostras de WAV PCM 16 bits
fix(fft): corrigir ordem dos bits na permutação
test(dsp): comparar FFT própria com numpy.fft
docs(requisitos): atualizar RF003 para espectro médio
chore: adicionar .gitignore
```

Regras:

- Um commit por mudança lógica. Evitar commits gigantes.
- Cada pessoa commita o que fez, com o próprio usuário configurado no Git.
- Se houver cartão no quadro de tarefas, citar o ID no corpo do commit ou no título do Pull Request (exemplo: `T10`).

## Branches e revisão

- `main` sempre deve estar funcionando.
- Cada tarefa em uma branch própria: `feat/rf001-upload`, `fix/janela-hamming`, `docs/artigo-metodologia`.
- Ao terminar, abrir um Pull Request. **O outro membro da dupla revisa** antes do merge (revisão cruzada).
- Depois do merge, apagar a branch.

## O que não vai para o repositório

Ambiente virtual (`venv`), arquivos `.db`, áudios enviados em `backend/uploads/`, senhas e arquivos de configuração pessoais. O `.gitignore` já cobre isso.

## Estilo de código

- Python: PEP 8.
- Nomes de funções e variáveis em inglês ou português, mas de forma consistente no projeto.
