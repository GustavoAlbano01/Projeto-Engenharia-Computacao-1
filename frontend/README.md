# Frontend

Interface em HTML, CSS e JavaScript (NF010), com o Plotly.js guardado nesta
pasta (sem CDN), para funcionar sem internet (NF011).

## Como abrir

O próprio Flask serve o frontend. Com o backend rodando:

```
cd backend
python run.py
```

abra **http://localhost:5000/** no navegador.

## Estrutura

```
frontend/
├── index.html        INT01 - envio do áudio e parâmetros (T23)
├── resultado.html    INT02 - resultado, aberto como resultado.html?id=N (T24, T25)
├── historico.html    INT03 - histórico e exclusão (T27, T28)
├── css/estilo.css    estilo comum das telas
├── js/api.js         chamadas à API (fetch) e tratamento de erros (NF002)
├── js/comum.js       mensagens, rótulos em português e formatação
└── vendor/
    └── plotly-2.35.2.min.js   biblioteca de gráficos (licença MIT, não editar)
```

## Regras

- Todas as chamadas à API passam por `js/api.js`; as telas não usam `fetch` direto.
- Mensagens de erro vêm do campo `message` do contrato (`docs/CONTRATO_API.md`)
  e são exibidas com `mostrarMensagem` (`js/comum.js`).
- Textos da interface em português (NF001).
- Nenhum arquivo externo (CDN): tudo é servido desta pasta (NF011).