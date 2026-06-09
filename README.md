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

## v3.2.1
- Correção: erro (KeyError) ao analisar equipamentos sem dados de posição (ex.: só CSV com GPS off). Mapa e mapa de calor agora pulam graciosamente equipamentos sem latitude/longitude e exibem aviso orientando subir o XLS.

## v3.3
- Mapa: seletor de **formato dos marcadores** das amostras (círculo, pino, quadrado, losango, triângulo); a referência mantém círculo azul.
- Mapa: hover das amostras agora exibe **erro, posição (lat/lon) e data/hora** (antes só a referência tinha data/hora).
- Mapa: **legenda reposicionada** (horizontal, acima do mapa) para não conflitar com os controles de zoom/download/reset.
- Migração para a engine de mapas mais recente do Plotly (Scattermap / density_map); requer plotly >= 5.24.

## v3.4
- Nova fonte **KML** (portal SSO/PST): traz o raio de incerteza calculado pelo sistema para cada posição estimada.
- Nova aba **Raio do Sistema**: valida se a posição real caiu dentro do raio informado pelo sistema (% de acerto), com gráfico distância × raio e lista dos pontos fora do raio.
- Coluna "% no Raio do Sistema" no resumo da Visão Geral e colunas raio_km / dentro_raio no Excel.
- "Como Usar" atualizado: card do KML, explicação do raio e exemplo de nomenclatura dos arquivos (mesmo nome, extensões .csv/.xls/.kml).
- Parser KML tolerante a encoding latin1; ignora placemarks de polígono (círculo do raio), extrai apenas o valor "Raio:".

## v3.4.1
- Correção: KeyError na aba Raio do Sistema. A coluna dentro_raio (object com True/False/None) é convertida para booleano antes da negação/filtragem, evitando erro de indexação no pandas.

## v3.5
- Tela de **login** (acesso restrito) com credenciais fixas provisórias. Bloqueia o app até autenticar.
- Botão **Sair** na barra lateral.
- Padrão visual Stoneridge na tela de login (logo, vermelho, layout centralizado).

Credenciais (provisórias, definidas em services/auth.py): usuário `validapst` · senha `123456`.

## v0.6
(Renumeração: a POC passa a usar versões abaixo de 1.0 por ainda não ser definitiva.)
- Login: subtítulo "Testes de Rodagem · Validação e Análise · Stoneridge Brasil".
- Cabeçalho do app: título "TESTE DE RODAGEM".
