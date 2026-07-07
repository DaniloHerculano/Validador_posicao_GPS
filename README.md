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

## v0.7
- Mapa: opção de exibir o **raio do sistema** (círculo de incerteza do KML) ao redor das amostras estimadas, habilitável/desabilitável **por equipamento**.
- Mapa: opção de **destacar em vermelho** as amostras que ficaram fora do raio do sistema.
- Círculo geodésico com erro de aproximação < 0,3%.

## v0.8
- Rede: análise de **frequência/banda do modem** (GSM850/900/1800/1900, LTE B3/B5/B7/B28...), com % por banda — útil para avaliar desempenho do modem em 2G e 4G.
- **Histórico de relatórios** via Google Drive: salvar os arquivos originais (CSV/XLS/KML) sob Projeto/Rota e reabrir depois (qualquer usuário logado). Requer configurar credenciais de conta de serviço do Google em st.secrets; sem isso, a aba exibe instruções e o restante do app funciona normalmente.

## v0.9
- Histórico reformulado para **leitura de pasta pública do Google Drive** (somente leitura, via API Key — sem conta de serviço, sem cota, sem custo).
- Modelo: cada subpasta da pasta de histórico = um teste (com CSV/XLS/KML). A equipe seleciona e o app baixa e roda a análise.
- Removida a dependência google-auth (não é mais necessária para API Key).

## v0.9.1
- Correção: o seletor de **Histórico** agora aparece logo no topo (seção Importar Arquivos), antes de carregar qualquer arquivo — permitindo abrir um teste salvo sem precisar enviar nada primeiro.
- Aba Histórico simplificada (aponta para o seletor do topo), evitando widgets duplicados.

## v0.9.2
- "Como Usar" atualizado com a seção **Histórico** (como abrir testes salvos no Drive e como adicionar novos) e a linha correspondente na tabela de abas.

## v0.10
- Suporte a rastreadores **mistos** (que ativaram o GPS durante a viagem, tendo pontos estimados E GPS real no mesmo arquivo): novo tipo "Misto", com métricas de erro separadas por tipo na aba Precisão e distinção visual no Mapa (GPS Real em verde × Estimada na cor do equipamento).
- Buffer/latência confirmado funcionando (Data Servidor − Data Módulo).
- Export (Excel) melhorado: nova aba **Informações** (capa com metadados e equipamentos), colunas nas abas de sincronização traduzidas e ampliadas (Tipo Posição, GPS Válido?, Banda, No Raio?, Endereço), cabeçalhos legíveis.

## v0.11
- Novo **modo Individual**: permite subir os arquivos de uma peça (ou várias) e inspecioná-las isoladamente — consumo de bateria, rede/operadora, banda, qualidade de GPS, movimento e latência — sem precisar de referência nem comparação de posição. Escolhido via seletor ao carregar os arquivos.
- Modo Comparativo (referência × amostras) permanece como estava.
- "Como Usar" atualizado com a explicação dos dois modos.

## v0.10.1
- Modo **Individual** confirmado e testado (inspecionar uma ou várias peças isoladamente — bateria, rede, banda, GPS, movimento, latência — sem exigir comparação).
- Correção técnica: substituído o parâmetro `use_container_width` (que o Streamlit removerá após 2025) por `width='stretch'`, evitando quebra futura. Versão mínima do Streamlit ajustada para 1.49.

## v0.10.2
- Correção no histórico: download de arquivos do Drive público passou a usar a URL direta (uc?export=download), mais robusta que o get_media+API Key, que retornava 403 ("automated queries"). Fallback para o método anterior mantido.

## v0.10.3
- **Correção importante nas análises técnicas (Rede, GPS, Latência):** passavam a contar apenas os registros do CSV que casaram no tempo com o XLS (via merge), subcontando pela metade. Agora usam o CSV técnico completo (df_tecnico), refletindo todos os registros. Ex.: 4G que aparecia como 213 agora mostra os 405 reais.
- **Correção de percentuais inconsistentes na aba Rede:** tecnologia e operadora usavam bases diferentes (uma excluía "Sem Sinal", outra não), fazendo os % não fecharem. Agora ambas usam a mesma base (total de registros técnicos), com legenda indicando a base.
- Confirmado: ausência de SMS nos dados é real (transmissão 100% UDP), não é falha.

## v0.11
- **Suporte ao arquivo único do Gerenciamento de Firmware:** um só CSV que contém tudo (posição, raio, estimada, endereço, rede/banda, bateria, latência, buffer). Detecção automática de formato — convive com o formato antigo de 3 arquivos (CSV+XLS+KML). Elimina a dependência do portal SSO.
  - Robustez a campos que variam por modelo/estado do GPS: usa "estimada" como base e infere a validade do GPS quando a coluna "gps" vem vazia (caso do RI720).
- **Buffer/LIFO na latência:** o cálculo de latência em tempo real agora exclui os registros recuperados do buffer (que sobem atrasados após perda de sinal e, por serem LIFO, têm data de servidor fora de ordem). Os bufferizados são contabilizados à parte e destacados na série temporal. Ex.: média real caiu de 24s (misturada) para 3,5s (só tempo real).

## v0.11.1
- "Como Usar" reescrito com a lógica correta das fontes: o **CSV do firmware sozinho já traz tudo** (recomendado); **XLS+KML do SSO** é alternativa parcial (sem rede/latência). Removida a informação desatualizada de que "o CSV não traz coordenada".
- Cada aba agora exibe uma **breve explicação** no topo (o que é analisado, como e de onde vêm os dados).
- Passo a passo e nomenclatura de arquivos atualizados para o novo fluxo (arquivo único primeiro).

## v0.11.2
- **Visão Geral reformulada** para ser um painel de entrada de verdade: KPIs do teste no topo (equipamentos, tipos, registros, erro global), tabela de equipamentos, resumo de precisão e uma seção **"Destaques por Área"** com rede predominante, operadora, banda, bateria (início→fim), latência real e buffer de cada peça. Funciona nos modos comparativo e individual.
- Descrição da ferramenta reescrita para refletir todo o escopo (posição, rede, GPS, bateria, movimento, latência/buffer, modos, histórico, export) — não apenas a comparação de posição.
