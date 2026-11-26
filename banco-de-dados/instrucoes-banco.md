# Banco de dados — Analisador Espectral de Áudio (AEA)

**SGBD:** SQLite 3 (arquivo único, sem servidor). Acesso pelo SQLAlchemy.
**Arquivo em uso:** `codigo-fonte/backend/instance/aea.db` (criado automaticamente).

## Tabelas

| Tabela | Função |
|---|---|
| `audios` | Arquivo WAV enviado (nome, caminho, taxa de amostragem, canais, nº de amostras, tamanho) |
| `analyses` | Resultado de cada análise (janela, tamanho do bloco, magnitudes, pico) — ligada a `audios` por `audio_id` |

Relacionamento: 1 áudio → N análises (`ON DELETE CASCADE`). Veja `diagrama-er.png`.

## Arquivos desta pasta

| Arquivo | Conteúdo |
|---|---|
| `schema.sql` | Criação das tabelas e índices (banco vazio) |
| `backup.sql` | Dump completo com 2 análises de exemplo (tom de 440 Hz e dois tons 440 + 1000 Hz) |
| `diagrama-er.png` / `.dot` | Diagrama entidade-relacionamento |

Não há `seed.sql`: o sistema não precisa de dados iniciais. O `backup.sql` faz esse papel de exemplo.

## Opção 1 — Criar o banco pelo próprio projeto (recomendado)

```bash
cd codigo-fonte/backend
python init_db.py
```

## Opção 2 — Importar o schema (banco vazio)

Com o utilitário `sqlite3` instalado:

```bash
sqlite3 codigo-fonte/backend/instance/aea.db < banco-de-dados/schema.sql
```

Sem o utilitário `sqlite3`, usando só o Python:

```bash
python -c "import sqlite3; c=sqlite3.connect('codigo-fonte/backend/instance/aea.db'); c.executescript(open('banco-de-dados/schema.sql',encoding='utf-8').read())"
```

## Opção 3 — Restaurar o backup (com dados de exemplo)

```bash
sqlite3 codigo-fonte/backend/instance/aea.db < banco-de-dados/backup.sql
```

ou, só com Python:

```bash
python -c "import sqlite3; c=sqlite3.connect('codigo-fonte/backend/instance/aea.db'); c.executescript(open('banco-de-dados/backup.sql',encoding='utf-8').read())"
```

> Crie antes a pasta `codigo-fonte/backend/instance/` se ela não existir.
> Os arquivos WAV originais do backup não estão incluídos; as análises
> aparecem no histórico, mas o áudio de origem não pode ser reaberto.
> Para gerar WAVs de teste: `python backend/tools/gerar_sinais.py`.

## Recomeçar do zero

```bash
cd codigo-fonte/backend
python init_db.py --reset   # pede confirmação e APAGA todo o histórico
```
