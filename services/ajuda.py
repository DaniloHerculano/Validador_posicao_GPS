"""
ajuda.py — Conteúdo da seção "Como usar" exibida na plataforma.
"""
import base64
from pathlib import Path
import streamlit as st
from services.ui import sec

_ASSETS = Path(__file__).parent.parent / "assets"


def _img_b64(nome: str) -> str:
    caminho = _ASSETS / nome
    if caminho.exists():
        return base64.b64encode(caminho.read_bytes()).decode()
    return ""


def _print_passo(nome_arquivo: str, legenda: str, estreito: bool = False):
    """Exibe um print de passo com moldura e legenda.
    estreito=True para imagens verticais/quadradas (limita largura e centraliza)."""
    b64 = _img_b64(nome_arquivo)
    if not b64:
        return
    classe = "print-step print-step-narrow" if estreito else "print-step"
    st.markdown(
        f'<div class="{classe}">'
        f'<img src="data:image/png;base64,{b64}" alt="{legenda}"/>'
        f'<div class="print-cap">{legenda}</div></div>',
        unsafe_allow_html=True)


def render_ajuda():
    sec("Como usar a plataforma")

    st.markdown("""
Esta ferramenta compara a posição de rastreadores com **GPS ligado** (posição real)
contra rastreadores com **GPS desligado** (posição estimada por antena de celular),
medindo o quão distante a estimativa ficou da referência real — e ainda valida se a
posição caiu **dentro do raio de incerteza que o próprio sistema** informa.
""")

    # ── Os três relatórios ──
    st.markdown("#### 📑 Os relatórios de cada rastreador")
    st.markdown("""
Cada equipamento gera relatórios que se complementam. Você pode subir os três
(análise completa) ou apenas os que tiver — o app usa o que estiver disponível.
""")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
<div class="help-card">
<div class="help-card-tag">.CSV</div>
<div class="help-card-title">Log Técnico</div>
<p>Rede (2G/3G/4G), operadora, satélites, DOP, latência, transmissão (UDP/SMS)
e bateria bruta.</p>
<p><b>Onde baixar:</b><br>
<a href="http://websites01.positronrt.cloud/firmware/index.php?tipoparametro=diversosplanform" target="_blank">
Portal de Firmware / Diversos</a></p>
</div>
""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
<div class="help-card">
<div class="help-card-tag">.XLS</div>
<div class="help-card-title">Relatório de Posição</div>
<p>Latitude/longitude (real <b>ou</b> estimada), endereço ("Próximo a:"),
posição estimada, validade do GPS e bateria em %.</p>
<p><b>Onde baixar:</b><br>
<a href="https://sso.pst.com.br/sso/" target="_blank">Portal SSO / PST</a></p>
</div>
""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
<div class="help-card">
<div class="help-card-tag">.KML</div>
<div class="help-card-title">Raio do Sistema</div>
<p>Além da posição, traz o <b>raio de incerteza</b> que o próprio sistema calcula
para cada posição estimada. Usado para validar o sistema PST.</p>
<p><b>Onde baixar:</b><br>
<a href="https://sso.pst.com.br/sso/" target="_blank">Portal SSO / PST</a> (mesmo
local do XLS, opção exportar KML)</p>
</div>
""", unsafe_allow_html=True)

    # ── Prints: onde extrair cada arquivo ──
    st.markdown("#### 📸 Onde extrair cada arquivo (passo a passo)")

    st.markdown("**CSV — [Portal de Firmware (Positron)]"
                "(http://websites01.positronrt.cloud/firmware/index.php?tipoparametro=diversosplanform):** "
                "acesse **Upload de arquivo → Diversos → Planilhas de Testes** (1, 2), "
                "escolha o tipo de consulta **\"Consulta carga posições e status\"** (3), "
                "informe o PIN e o período em UTC (4) e clique em **Consultar** (5).")
    _print_passo("config_websites01.png",
                 "Portal de Firmware — geração da planilha CSV (Planilhas de Testes)",
                 estreito=True)

    st.markdown("**XLS e KML — [Portal SSO/PST](https://sso.pst.com.br/sso/):** "
                "na busca (1), marque **Localização** e "
                "**Posições estimadas** (2, 3), defina data/hora inicial e final e clique "
                "em **Consultar** (4).")
    _print_passo("config_sso.png",
                 "Portal SSO/PST — filtro de consulta (Localização + Posições estimadas)")

    st.markdown("Na aba **Resultado**, use **Exportar XLS** (1) para o relatório de posição "
                "e **Exportar KML** (2) para obter o arquivo com o raio do sistema.")
    _print_passo("download_xls_kml_sso.png",
                 "Portal SSO/PST — exportação do XLS e do KML")

    # ── Por que dois ──
    st.markdown("#### 🔗 Por que vários relatórios?")
    st.markdown("""
O **CSV** sabe *como* o equipamento está se comunicando (rede, sinal, bateria), mas
quando o GPS está desligado ele **não traz a coordenada pronta** — só o código da
torre de celular usada.

O **XLS** é gerado por um sistema que converte essa torre em latitude/longitude
(a posição estimada com o endereço "Próximo a:"). É a fonte confiável de **onde** o
equipamento está.

Por isso o app **une as fontes por horário**: usa a posição e a bateria do XLS,
enriquece cada ponto com os dados técnicos do CSV, e associa o raio de incerteza
do KML — tudo pelo horário mais próximo.
""")

    # ── O KML e o raio ──
    st.markdown("#### 🎯 O KML e o raio do sistema")
    st.markdown("""
O **KML** (extraído do portal SSO/PST, no mesmo local do XLS) contém, para cada
posição estimada, o **raio de incerteza** que o próprio sistema calcula — no arquivo
aparece como, por exemplo, `Raio: 3012.0` (em metros; o app converte para km).

Esse raio representa a área onde o sistema afirma que o rastreador deveria estar.
A aba **Raio do Sistema** verifica, no mesmo horário já analisado, se a posição real
(da referência) caiu **dentro desse raio** — informando o percentual de acerto do
próprio sistema. É uma forma de validar o sistema de geolocalização atual.

> Sem o KML, todas as demais análises continuam funcionando; apenas a validação
> contra o raio do sistema fica indisponível.
""")

    # ── Exemplo de nomes ──
    st.markdown("#### 📁 Como nomear os arquivos")
    st.markdown("""
Os arquivos de um mesmo rastreador devem ter o **mesmo nome**, mudando apenas a
**extensão**. Assim o app agrupa as fontes automaticamente. Exemplo para um
equipamento:
""")
    st.code(
        "RI130_623721833_GNSS_1_29_05-01_06.csv   ← log técnico\n"
        "RI130_623721833_GNSS_1_29_05-01_06.xls   ← posição\n"
        "RI130_623721833_GNSS_1_29_05-01_06.kml   ← raio do sistema",
        language="text")
    st.markdown("""
Repita o padrão para cada rastreador (mesmo nome-base, extensões `.csv`, `.xls`,
`.kml`). Não é obrigatório ter as três — suba as que tiver.
""")

    # ── Passo a passo ──
    st.markdown("#### 🚀 Passo a passo")
    st.markdown("""
1. **Baixe os relatórios** de cada rastreador (CSV no portal de firmware; XLS e KML
   no portal SSO/PST).
2. **Mantenha o mesmo nome** para os arquivos do mesmo equipamento — só muda a
   extensão (`.csv`, `.xls`, `.kml`). O app os une automaticamente.
3. **Suba os arquivos** na seção *Importar Arquivos*.
4. **Escolha a referência** (o rastreador com GPS ligado, normalmente o RI130) e
   marque quais comparar.
5. **Ajuste na barra lateral** a tolerância de horário e os raios de precisão
   (1 / 3 / 5 km, editáveis).
6. Clique em **Iniciar Análise Completa** e navegue pelas abas.
7. Na aba **Dados & Export**, baixe o Excel com tabelas e gráficos.
""")

    # ── O que cada aba mostra ──
    st.markdown("#### 📊 O que cada aba mostra")
    st.markdown("""
| Aba | Conteúdo | Precisa de |
|-----|----------|------------|
| **Visão Geral** | Resumo comparativo e erro médio | XLS (posição) |
| **Mapa** | Pontos no mapa + linhas de erro + calor | XLS (posição) |
| **Precisão GPS** | Erro em km, % por raio, endereços de maior erro | XLS (posição) |
| **Raio do Sistema** | % de pontos dentro do raio que o sistema informa | KML + XLS |
| **Rede & Operadora** | 2G/3G/4G, operadora, banda/frequência, UDP/SMS | CSV (técnico) |
| **Qualidade GPS** | Satélites, DOP, altitude | CSV (técnico) |
| **Movimento** | Velocidade, direção, sensor | CSV + XLS |
| **Bateria** | Nível e consumo | XLS ou CSV |
| **Latência** | Tempo módulo→servidor, buffer | CSV (técnico) |
""")

    # ── Como o erro é medido ──
    st.markdown("#### 📐 Como o erro é medido")
    st.markdown("""
A distância entre o ponto estimado e o real é a **distância geodésica** (linha reta
sobre a curvatura da Terra, modelo WGS-84 — o mesmo do GPS). O app pareia cada ponto
estimado com o ponto real de **horário mais próximo** (dentro da tolerância) e mede
essa distância em km.

> **Atenção:** se os equipamentos estavam em movimento, parte do erro pode ser o
> deslocamento real do veículo entre os dois horários, não falha da estimativa. A
> coluna `dif_seg` nos dados sincronizados mostra essa defasagem de tempo.
""")

    st.caption("Stoneridge Brasil · Validador de Posicionamento")


HELP_CSS = """
<style>
.help-card{background:#ffffff;border:1px solid #dce4ee;border-top:3px solid #dd0933;
  border-radius:10px;padding:1.1rem 1.3rem;height:100%;box-shadow:0 1px 3px rgba(44,57,70,.05);}
.help-card-tag{display:inline-block;background:#dd0933;color:#fff;font-family:'Barlow Condensed',sans-serif;
  font-weight:700;font-size:.72rem;letter-spacing:.1em;padding:2px 10px;border-radius:5px;margin-bottom:.5rem;}
.help-card-title{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:1.25rem;
  color:#2c3946;margin-bottom:.5rem;}
.help-card p{font-size:.86rem;color:#3a4a57;margin:.4rem 0;}
.help-card a{color:#dd0933;font-weight:600;text-decoration:none;}
.help-card a:hover{text-decoration:underline;}
.print-step{margin:.6rem 0 1.2rem 0;border:1px solid #dce4ee;border-radius:10px;
  overflow:hidden;background:#fff;box-shadow:0 1px 3px rgba(44,57,70,.06);}
.print-step img{width:100%;display:block;border-bottom:1px solid #eef2f7;}
.print-step-narrow img{max-width:380px;width:100%;margin:0 auto;border-bottom:none;}
.print-step-narrow{text-align:center;}
.print-step-narrow .print-cap{border-top:1px solid #eef2f7;text-align:left;}
.print-cap{font-size:.74rem;color:#6b7f8f;padding:.5rem .8rem;background:#f9fafb;}
</style>
"""
