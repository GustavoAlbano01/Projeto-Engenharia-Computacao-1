# Backend

API REST em Flask. Responsável por:

- receber e validar arquivos WAV (PCM 16 bits, até 60 MB);
- aplicar janelas (retangular, Hanning, Hamming);
- calcular a FFT (implementação própria, radix-2) e o espectro médio;
- gravar e consultar análises no SQLite.

Contrato da API: ver a Tabela 1 do documento de requisitos em `docs/requisitos/`.

Pasta `uploads/`: arquivos de áudio enviados (o conteúdo não é versionado).

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
* **Windows:**
```powershell
  .\.venv\Scripts\activate
```

* **Linux:**
```bash
  source .venv/bin/activate
```

### 3. Instalar as Dependências
```bash
pip install -r .\requirements.txt
```