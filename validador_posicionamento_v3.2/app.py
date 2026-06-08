"""
app.py — Validador de Posicionamento (Stoneridge Brasil)
Aceita CSV (log técnico) e XLS (posição estimada convertida) por equipamento,
funde as duas fontes e gera análise comparativa completa.
"""
import streamlit as st

st.set_page_config(page_title="Validador de Posicionamento", page_icon="📡",
                   layout="wide", initial_sidebar_state="expanded")

from services.ui import carregar_css, sec, badge, logo_sidebar
from services.config import SR_RED
from services.loader import consolidar_equipamento, nome_base, extrair_pin, extrair_modelo
from services.analise import sincronizar
from services.export import gerar_excel, nome_arquivo_seguro
from services.ajuda import render_ajuda, HELP_CSS
from services import graficos as g
import pandas as pd

carregar_css()
st.markdown(HELP_CSS, unsafe_allow_html=True)

st.markdown("""
<div class="hero-wrap"><div class="hero-bar"></div><div>
<div class="hero-title">VALIDADOR DE POSICIONAMENTO</div>
<div class="hero-sub">Análise comparativa GPS Real × Posição Estimada · Stoneridge Brasil</div>
</div></div>""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_sidebar()
    st.markdown("### ⚙️ Parâmetros")
    st.markdown("---")
    tolerancia = st.number_input("Tolerância de horário (min)", 1, 60, 10, 1,
        help="Janela máxima para parear referência × comparado")
    tol_fusao = st.number_input("Tolerância de fusão CSV↔XLS (s)", 5, 300, 60, 5,
        help="Janela para casar o log técnico (CSV) ao ponto de posição (XLS)")
    st.markdown("**Raios de precisão (km)**")
    raio1 = st.number_input("Raio 1 (km)", value=1.0, step=0.5, min_value=0.1)
    raio2 = st.number_input("Raio 2 (km)", value=3.0, step=0.5, min_value=0.1)
    raio3 = st.number_input("Raio 3 (km)", value=5.0, step=0.5, min_value=0.1)
    st.markdown("---")
    st.markdown('<span style="font-size:.68rem;color:#4a5568">Stoneridge Brasil · v3.2</span>',
                unsafe_allow_html=True)

# ── AJUDA RÁPIDA ──────────────────────────────────────────────────────────────
with st.expander("❓ Primeira vez aqui? Veja como usar a plataforma"):
    render_ajuda()

# ── UPLOAD ────────────────────────────────────────────────────────────────────
sec("01 · Importar Arquivos")
st.caption("Envie o **CSV** (log técnico) e/ou o **XLS** (posição convertida) de cada "
           "rastreador. Arquivos com o mesmo nome (extensão diferente) são unidos automaticamente. "
           "Pode subir só um dos dois — o app mostra o que for possível com o que tiver.")
arquivos = st.file_uploader("Arquivos dos rastreadores",
    type=["csv", "xls", "xlsx"], accept_multiple_files=True)

if not arquivos:
    st.info("⬆️  Envie os arquivos (CSV e/ou XLS) para iniciar a análise. "
            "Abra o guia acima se for sua primeira vez.")
    st.stop()

# Agrupa por nome-base
grupos = {}
for arq in arquivos:
    base = nome_base(arq.name)
    ext = arq.name.lower().rsplit(".", 1)[-1]
    grupos.setdefault(base, {"csv": None, "xls": None})
    grupos[base]["csv" if ext == "csv" else "xls"] = arq

# Consolida cada equipamento
dados = []
for base, fontes in grupos.items():
    try:
        info = consolidar_equipamento(base, fontes["csv"], fontes["xls"], tol_fusao=tol_fusao)
        dados.append(info)
    except Exception as e:
        st.error(str(e))
if not dados:
    st.stop()

# ── TABELA DE ARQUIVOS ────────────────────────────────────────────────────────
sec("02 · Equipamentos Carregados")
rows = "".join(
    f"<tr><td style='font-family:Barlow Condensed'>{d['modelo']}</td>"
    f"<td style='font-family:Barlow Condensed;color:{SR_RED};font-weight:700'>{d['pin']}</td>"
    f"<td>{badge(d['tipo'])}</td>"
    f"<td style='font-family:Barlow Condensed;color:#6b7f8f'>{d['fonte']}</td>"
    f"<td style='text-align:right;font-family:Barlow Condensed'>{d['registros']:,}</td></tr>"
    for d in dados)
st.markdown(f'<table class="file-table"><thead><tr><th>Modelo</th><th>PIN</th>'
    f'<th>Tipo</th><th>Fonte</th><th style="text-align:right">Registros</th></tr></thead>'
    f'<tbody>{rows}</tbody></table>', unsafe_allow_html=True)

# ── SELEÇÃO ───────────────────────────────────────────────────────────────────
sec("03 · Configurar Comparação")
def rotulo(d):
    return f"{d['modelo']} · {d['pin']}"
mapa_rotulo = {rotulo(d): d["arquivo"] for d in dados}

reais = [rotulo(d) for d in dados if d["tipo"] == "GPS Real"]
todos = [rotulo(d) for d in dados]
cand = reais if reais else todos

cR, cC = st.columns([1, 2])
with cR:
    ref_rot = st.selectbox("🔵 Referência (GPS Real)", cand,
        help="Rastreador com GPS ligado — geralmente o RI130")
with cC:
    opc = [r for r in todos if r != ref_rot]
    comp_rot = st.multiselect("🟠 Comparar com", opc, default=opc)

referencia = mapa_rotulo[ref_rot]
comparacao = [mapa_rotulo[r] for r in comp_rot]

if not comparacao:
    st.warning("Selecione ao menos um rastreador para comparar.")
    st.stop()

btn = st.button("🚀  INICIAR ANÁLISE COMPLETA")
if not btn and "resultados" not in st.session_state:
    st.stop()

if btn:
    ref_item = next(d for d in dados if d["arquivo"] == referencia)
    df_ref = ref_item["df"].copy()
    resultados = {}
    with st.spinner("Sincronizando e calculando distâncias..."):
        for nome in comparacao:
            item = next(d for d in dados if d["arquivo"] == nome)
            resultados[nome] = sincronizar(df_ref, item["df"].copy(), tolerancia)
    st.session_state.update({"resultados": resultados, "ref_nome": referencia,
        "ref_df": df_ref, "comparacao": comparacao, "raios": (raio1, raio2, raio3),
        "dados_meta": {d["arquivo"]: {k: d[k] for k in ("modelo","pin","tipo","fonte")} for d in dados}})

resultados = st.session_state.get("resultados", {})
df_ref = st.session_state.get("ref_df", pd.DataFrame())
comparacao = st.session_state.get("comparacao", [])
raios = st.session_state.get("raios", (1.0, 3.0, 5.0))
ref_nome = st.session_state.get("ref_nome", "")
if not resultados:
    st.stop()

# Avisos sobre sincronizações vazias
vazios = [n for n, r in resultados.items() if len(r) == 0]
if vazios:
    st.warning("Sem sincronização para: " + ", ".join(vazios) +
               ". Verifique se há sobreposição de horário ou aumente a tolerância.")

# ── ABAS ──────────────────────────────────────────────────────────────────────
abas = st.tabs(["📊 Visão Geral", "🗺 Mapa", "📍 Precisão GPS", "📶 Rede & Operadora",
    "🛰 Qualidade GPS", "🚗 Movimento", "🔋 Bateria", "⏱ Latência", "📋 Dados & Export",
    "❓ Como Usar"])

with abas[0]: g.aba_visao_geral(resultados, df_ref, ref_nome, raios)
with abas[1]: g.aba_mapa(resultados, df_ref, ref_nome)
with abas[2]: g.aba_precisao(resultados, raios)
with abas[3]: g.aba_rede(resultados, df_ref, ref_nome, comparacao, dados)
with abas[4]: g.aba_qualidade_gps(df_ref, ref_nome, comparacao, dados)
with abas[5]: g.aba_movimento(df_ref, ref_nome, comparacao, dados)
with abas[6]: g.aba_bateria(df_ref, ref_nome, comparacao, dados)
with abas[7]: g.aba_latencia(df_ref, ref_nome, comparacao, dados)
with abas[9]: render_ajuda()

with abas[8]:
    sec("Exportar Análise Completa")
    st.caption("Excel com Resumo, dados sincronizados por equipamento e consolidado Rede & Bateria.")
    df_resumo = st.session_state.get("df_resumo")
    cE1, cE2 = st.columns(2)
    with cE1:
        st.download_button("📥  Baixar Excel Completo (.xlsx)",
            data=gerar_excel(df_resumo, resultados, dados, raios=raios),
            file_name="analise_posicionamento.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_excel")
    with cE2:
        if df_resumo is not None:
            st.download_button("📥  Baixar Resumo (.csv)",
                data=df_resumo.to_csv(index=False).encode("utf-8"),
                file_name="resumo_posicionamento.csv", mime="text/csv", key="dl_csv")

    sec("Registros Sincronizados")
    for nome, df in resultados.items():
        st.markdown(f"**{nome}** — {len(df)} sincronizações")
        if len(df) > 0:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(f"📥 CSV — {nome}",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"sync_{nome_arquivo_seguro(nome)}.csv",
                mime="text/csv", key=f"dlc_{nome}")
        else:
            st.warning("Sem registros sincronizados.")

    sec("Dados Consolidados por Equipamento")
    sel = st.selectbox("Equipamento", [d["arquivo"] for d in dados], key="sel_bruto")
    item = next(d for d in dados if d["arquivo"] == sel)
    cols = [c for c in item["df"].columns if not c.startswith("_")]
    st.dataframe(item["df"][cols].head(1000), use_container_width=True, hide_index=True)
    st.caption(f"Fonte: {item['fonte']} · até 1000 de {len(item['df'])} registros · PIN {item['pin']}")
