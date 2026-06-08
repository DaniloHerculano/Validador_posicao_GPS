"""
ajuda.py — Conteúdo da seção "Como usar" exibida na plataforma.
"""
import streamlit as st
from services.ui import sec


def render_ajuda():
    sec("Como usar a plataforma")

    st.markdown("""
Esta ferramenta compara a posição de rastreadores com **GPS ligado** (posição real)
contra rastreadores com **GPS desligado** (posição estimada por antena de celular),
medindo o quão distante a estimativa ficou da referência real.
""")

    # ── Os dois relatórios ──
    st.markdown("#### 📑 Os dois relatórios de cada rastreador")
    st.markdown("""
Cada equipamento gera **dois arquivos** que se complementam. Você pode subir os dois
(análise completa) ou apenas um (análise parcial — o app usa o que tiver).
""")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
<div class="help-card">
<div class="help-card-tag">.CSV</div>
<div class="help-card-title">Log Técnico</div>
<p>Traz os dados de engenharia do equipamento: rede (2G/3G/4G), operadora,
satélites, DOP, latência, tipo de transmissão (UDP/SMS) e bateria bruta.</p>
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
<p>Traz a posição já convertida em latitude/longitude (real <b>ou</b> estimada),
o endereço ("Próximo a:"), se a posição é estimada, a validade do GPS e a
bateria em %.</p>
<p><b>Onde baixar:</b><br>
<a href="https://sso.pst.com.br/sso/" target="_blank">
Portal SSO / PST</a></p>
</div>
""", unsafe_allow_html=True)

    # ── Por que dois ──
    st.markdown("#### 🔗 Por que dois relatórios?")
    st.markdown("""
O **CSV** sabe *como* o equipamento está se comunicando (rede, sinal, bateria), mas
quando o GPS está desligado ele **não traz a coordenada pronta** — só o código da
torre de celular usada.

O **XLS** é gerado por um sistema que converte essa torre em latitude/longitude
(a posição estimada com o endereço "Próximo a:"). É a fonte confiável de **onde** o
equipamento está.

Por isso o app **une os dois por horário**: usa a posição e a bateria do XLS, e
enriquece cada ponto com os dados técnicos do CSV mais próximo no tempo.
""")

    # ── Passo a passo ──
    st.markdown("#### 🚀 Passo a passo")
    st.markdown("""
1. **Baixe os relatórios** de cada rastreador nos portais acima (CSV e/ou XLS).
2. **Mantenha o mesmo nome** para o par CSV+XLS do mesmo equipamento — só muda a
   extensão. O app os une automaticamente.
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
| **Rede & Operadora** | 2G/3G/4G, operadora, UDP/SMS | CSV (técnico) |
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
</style>
"""
