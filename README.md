# Analisador Espectral de Áudio (AEA)

Projeto da disciplina **Projetos em Engenharia da Computação I** (UNIVAP – FEAU).

Sistema web, executado localmente, que lê um arquivo de áudio WAV, aplica janelamento (retangular, Hanning ou Hamming), calcula o espectro de frequências com uma **FFT implementada no próprio projeto** e exibe o resultado em um gráfico interativo. As análises ficam salvas em um banco SQLite, com histórico.

## Equipe

- Eduardo Peron
- Gustavo Albano Nunes
- Orientador: Prof. Me. Hélio Esperidião

## Estrutura do repositório

```
backend/    API Flask, leitura de WAV, janelas, FFT e banco SQLite
frontend/   Interface web (HTML, CSS, JavaScript e Plotly.js local)
tests/      Testes automatizados (pytest)
docs/       Documento de requisitos, artigo INIC, diagramas e decisões
```

## Tecnologias

- Python 3.10 ou superior, Flask, Flask-CORS, SQLAlchemy, SQLite, NumPy
- HTML, CSS e JavaScript, com Plotly.js distribuído localmente (o sistema funciona sem internet)
- SciPy e pytest apenas para testes e conferência

## Como executar

*Em construção.* As instruções de instalação e execução serão adicionadas quando o backend base estiver pronto.

## Documentação

- Requisitos: `docs/requisitos/`
- Artigo no padrão INIC: `docs/artigo/`
- Decisões de projeto: `docs/decisoes.md`
- Convenções de commits e fluxo de trabalho: `CONTRIBUTING.md`
