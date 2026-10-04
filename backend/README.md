# Backend

API REST em Flask. Responsável por:

- receber e validar arquivos WAV (PCM 16 bits, até 60 MB);
- aplicar janelas (retangular, Hanning, Hamming);
- calcular a FFT (implementação própria, radix-2) e o espectro médio;
- gravar e consultar análises no SQLite.

Contrato da API: [`docs/CONTRATO_API.md`](../docs/CONTRATO_API.md) (especificação completa).
A Tabela 1 do documento de requisitos em `docs/requisitos/` traz um resumo.

Pasta `uploads/`: arquivos de áudio enviados (o conteúdo não é versionado).

## Estado atual

As rotas já seguem o contrato v1 (validação dos parâmetros e formato dos erros),
mas devolvem **dados de mock** (`mocks/`), guardados em memória. Os pontos que
ainda serão implementados estão marcados com `TODO` no código:

- leitura real do WAV (cabeçalho RIFF/WAVE e metadados);
- janelamento, FFT radix-2 e espectro médio;
- ligação das rotas ao banco (os modelos e o script de criação já existem);
- espectrograma (RF006, desejável — hoje responde 501).

## Estrutura

```
backend/
├── run.py              ponto de entrada do servidor
├── init_db.py          script que cria o banco SQLite
├── requirements.txt
├── mocks/              exemplos de resposta do contrato
├── uploads/            áudios enviados (não versionado)
├── instance/           aea.db, o banco SQLite (não versionado)
└── app/
    ├── __init__.py     create_app(): CORS, limite de upload, rotas
    ├── contract.py     constantes do contrato (janelas, blocos, limite)
    ├── errors.py       envelope único de erro
    ├── database.py     conexão SQLite e criação das tabelas
    ├── models.py       tabelas audios e analyses
    ├── mock_store.py   armazenamento temporário em memória
    └── routes/
        ├── audios.py   POST /api/audios
        └── analyses.py /api/analyses (POST, GET, DELETE, espectrograma)
```

## Configuração e Instalação

Siga os passos abaixo para configurar o ambiente e instalar as dependências necessárias.

### 0. Entrar na pasta do backend
```bash
cd backend
```

### 1. Criar o Ambiente Virtual
```bash
python -m venv .venv
```

### 2. Ativar o Ambiente Virtual
* **Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

* **Linux:**
```bash
source .venv/bin/activate
```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

## Banco de dados

Com o ambiente virtual ativo, dentro de `backend/`:

```bash
python init_db.py
```

Cria `instance/aea.db` com as tabelas `audios` e `analyses`. Pode ser rodado
mais de uma vez: só cria o que falta e não apaga dados.

Para apagar todo o histórico e recriar as tabelas (pede confirmação):

```bash
python init_db.py --reset
```

## Executar

Com o ambiente virtual ativo, dentro de `backend/`:

```bash
python run.py
```

A API fica disponível em `http://localhost:5000/api`. Teste rápido: abrir
`http://localhost:5000/api/analyses` no navegador deve mostrar `[]`.

## Testes

Com o ambiente virtual ativo, **na raiz do repositório**:

```bash
python -m pytest -q
```
