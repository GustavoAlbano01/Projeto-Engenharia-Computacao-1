# Analisador Espectral de Áudio (AEA)

Projeto da disciplina **Projetos em Engenharia da Computação I** (UNIVAP – FEAU).

Sistema web, executado localmente, que lê um arquivo de áudio WAV, aplica janelamento (retangular, Hanning ou Hamming), calcula o espectro de frequências com uma **FFT implementada no próprio projeto** e exibe o resultado em um gráfico interativo. As análises ficam salvas em um banco SQLite, com histórico.

## Equipe

- Eduardo Peron — API Flask e contrato JSON, leitura/validação de WAV, banco SQLite (modelos e DbStore), telas do frontend (início, histórico, exclusão), espectrograma, medição de tempo de resposta, testes de integração e documento de requisitos
- Gustavo Albano Nunes — núcleo DSP (DFT, FFT radix-2, janelas, espectro e pico), gerador de sinais de teste, gráfico e interação da tela de resultado, validação (tabela de picos, vazamento espectral, benchmark DFT × FFT)
- Orientador: Prof. Me. Hélio Esperidião

## Estrutura do repositório

```
backend/    API Flask, leitura de WAV, janelas, FFT e banco SQLite
frontend/   Interface web (HTML, CSS, JavaScript e Plotly.js local)
tests/      Testes automatizados (pytest)
docs/       Documento de requisitos, artigo INIC, diagramas e decisões
```

## Tecnologias

- Python 3.12 ou superior, Flask, Flask-CORS, SQLAlchemy, SQLite, NumPy, Matplotlib (imagem do espectrograma)
- HTML, CSS e JavaScript, com Plotly.js distribuído localmente (o sistema funciona sem internet)
- SciPy e pytest apenas para testes e conferência

## Como executar

Os comandos abaixo são para o PowerShell (Windows). No Linux, troque a
ativação do ambiente por `source .venv/bin/activate`.

### 1. Pré-requisito

Python 3.12 ou superior (`python --version`). Para rodar o sistema não é
preciso internet depois da instalação (NF011).

### 2. Instalar (uma vez só, na raiz do repositório)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

Se o PowerShell bloquear a ativação, rode antes
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

### 3. Criar o banco de dados (uma vez só)

```powershell
cd backend
python init_db.py
```

Cria `backend/instance/aea.db`. Pode ser repetido sem perder dados.

### 4. Iniciar o sistema

Ainda dentro de `backend/`, com o ambiente ativo:

```powershell
python run.py
```

O Flask serve a API e o frontend. Abra **http://localhost:5000/** no
navegador, envie um arquivo WAV (PCM 16 bits, até 60 MB), escolha janela e
tamanho de bloco e veja o espectro. As análises ficam no histórico.

Para encerrar, pressione `Ctrl+C` no terminal.

### 5. Rodar os testes (opcional)

Na raiz do repositório, com o ambiente ativo:

```powershell
python -m pytest -q
```

### 6. Sinais de referência (opcional)

Para gerar WAV com tons de frequência conhecida e testar o sistema, veja
`backend/README.md` (seção "Sinais de teste"). Os resultados da validação
estão em `docs/resultados/`.

### Problemas comuns

| Sintoma | Causa provável |
|---|---|
| `ModuleNotFoundError: flask_cors` (ou outro módulo) | Ambiente não ativado ou `pip install` não executado |
| `python` não é reconhecido | Python não está no PATH; reinstale marcando "Add to PATH" |
| Erro ao instalar NumPy ou SciPy | Python anterior à 3.12 |
| Porta 5000 ocupada | Outro programa usa a porta; feche-o e rode `python run.py` de novo |
| Página abre mas o histórico vem vazio | Normal na primeira execução: ainda não há análises |

## Documentação

- Requisitos: `docs/requisitos/`
- Artigo no padrão INIC: `docs/artigo/`
- Decisões de projeto: `docs/decisoes.md`
- Convenções de commits e fluxo de trabalho: `CONTRIBUTING.md`

## Banco de dados

SQLite, criado por `python backend/init_db.py` (cria `backend/instance/aea.db`).
Nos arquivos da entrega, o schema, o backup, o diagrama ER e as instruções de
restauração estão em `banco-de-dados/` (`schema.sql`, `backup.sql`,
`diagrama-er.png`, `instrucoes-banco.md`).

## Referências

Ver `referencias/referencias-abnt.pdf` (na entrega) e a seção Referências do
artigo em `docs/artigo/`.

## Repositório

https://github.com/GustavoAlbano01/Projeto-Engenharia-Computacao-1
