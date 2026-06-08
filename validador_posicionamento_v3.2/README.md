# 📡 Validador de Posicionamento — v3.2

Análise comparativa de rastreadores GPS Real × Posição Estimada · Stoneridge Brasil

## Novidades da v3.2
- **Tema claro** (fundo branco) com identidade visual Stoneridge
- **Logo** no topo da barra lateral
- Título do cabeçalho corrigido (não corta mais)
- **Painéis expansíveis por rastreador**: cada equipamento fica recolhido; clique para expandir (vários ao mesmo tempo se quiser). A referência abre expandida por padrão.
- **Excel com gráficos nativos**: barras de erro médio, % por raio, tecnologia por equipamento e linha de erro no tempo embutidos nas planilhas

## Dupla fonte CSV + XLS
- **CSV** — log técnico (rede, satélites, DOP, latência, transmissão, bateria bruta)
- **XLS** — posição convertida (lat/lon real ou estimada por ERB, endereço "Próximo a:", bateria %, validade)

O app agrupa por nome-base e funde por horário (`merge_asof`). Posição/bateria vêm do XLS; dados técnicos do CSV.

## Estrutura
```
projeto/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/config.toml      # tema claro
├── assets/stoneridge_logo.png  # logo (fundo transparente)
└── services/
    ├── config.py    ├── loader.py   ├── analise.py
    ├── ui.py        ├── export.py   └── graficos.py
```

## Instalação
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Nota técnica
A "bateria fantasma" do RI130 (valores 253) ocorre porque ele opera com a fonte
conectada (carregando), enquanto os demais desligam ao conectar a fonte. Valores
fora de 0–20 no CSV são descartados; o XLS (em %) tem prioridade.

## Operadoras (networkinfo)
| Código | Operadora |
|--------|-----------|
| 72402-72454, 72406 | TIM |
| 72405, 72438 | Claro |
| 72410, 72411, 72423, 72431, 72432 | Vivo |

---
Stoneridge Brasil · v3.2

## v3.2
- Seção **"Como Usar"** dentro da plataforma (aba dedicada + guia rápido no topo)
- Links diretos para baixar cada relatório:
  - CSV (log técnico): http://websites01.positronrt.cloud/firmware/index.php?tipoparametro=diversosplanform
  - XLS (posição): https://sso.pst.com.br/sso/
- Mensagens contextuais indicando qual arquivo subir para destravar cada análise
- Upload parcial (só CSV ou só XLS) totalmente suportado
