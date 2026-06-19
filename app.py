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
from services.auth import exigir_login, botao_sair
from services import graficos as g
import pandas as pd

carregar_css()

# Gate de acesso — exige login antes de qualquer conteúdo
exigir_login()

st.markdown(HELP_CSS, unsafe_allow_html=True)

st.markdown("""
<div class="hero-wrap"><div class="hero-bar"></div><div>
<div class="hero-title">TESTE DE RODAGEM</div>
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
    botao_sair()
    st.markdown('<span style="font-size:.68rem;color:#4a5568">Stoneridge Brasil · v0.8</span>',
                unsafe_allow_html=True)

# ── AJUDA RÁPIDA ──────────────────────────────────────────────────────────────
with st.expander("❓ Primeira vez aqui? Veja como usar a plataforma"):
    render_ajuda()

# ── UPLOAD ────────────────────────────────────────────────────────────────────
sec("01 · Importar Arquivos")
st.caption("Envie o **CSV** (log técnico), o **XLS** (posição) e/ou o **KML** (raio) de cada "
           "rastreador. Arquivos com o mesmo nome (extensão diferente) são unidos automaticamente. "
           "Pode subir só parte deles — o app mostra o que for possível com o que tiver.")

# Fonte de dados: upload manual OU carregado do histórico (Drive)
import io as _io
from services import historico as hist

# Se o usuário escolheu abrir um item do histórico, os bytes ficam em session_state
fonte_bytes = st.session_state.get("hist_arquivos")  # dict {nome: bytes} ou None
fonte_label = st.session_state.get("hist_label")

arquivos = st.file_uploader("Arquivos dos rastreadores",
    type=["csv", "xls", "xlsx", "kml"], accept_multiple_files=True)

if fonte_bytes:
    st.success(f"📂 Carregado do histórico: **{fonte_label}**  ·  {len(fonte_bytes)} arquivo(s). "
               "Para voltar ao envio manual, use o botão abaixo.")
    if st.button("↩ Limpar e enviar manualmente"):
        st.session_state.pop("hist_arquivos", None)
        st.session_state.pop("hist_label", None)
        st.rerun()

# Monta dict unificado {nome: bytes} a partir do upload ou do histórico
arquivos_bytes = {}
if arquivos:
    for arq in arquivos:
        arquivos_bytes[arq.name] = arq.getvalue()
elif fonte_bytes:
    arquivos_bytes = dict(fonte_bytes)

if not arquivos_bytes:
    st.info("⬆️  Envie os arquivos (CSV, XLS e/ou KML) ou abra um relatório salvo na aba **Histórico**.")
    st.stop()

# Agrupa por nome-base
grupos = {}
for nome_arq, conteudo in arquivos_bytes.items():
    base = nome_base(nome_arq)
    ext = nome_arq.lower().rsplit(".", 1)[-1]
    grupos.setdefault(base, {"csv": None, "xls": None, "kml": None})
    bio = _io.BytesIO(conteudo)
    bio.name = nome_arq
    if ext == "csv":
        grupos[base]["csv"] = bio
    elif ext == "kml":
        grupos[base]["kml"] = bio
    else:  # xls, xlsx
        grupos[base]["xls"] = bio

# Consolida cada equipamento
dados = []
for base, fontes in grupos.items():
    try:
        info = consolidar_equipamento(base, fontes["csv"], fontes["xls"],
                                      kml_file=fontes["kml"], tol_fusao=tol_fusao)
        dados.append(info)
    except Exception as e:
        st.error(str(e))
if not dados:
    st.stop()

# Guarda os bytes originais para permitir salvar no histórico depois
st.session_state["arquivos_bytes_atuais"] = arquivos_bytes

# ── TABELA DE ARQUIVOS ────────────────────────────────────────────────────────
sec("02 · Equipamentos Carregados")
rows = "".join(
    f"<tr><td style='font-family:Barlow Condensed'>{d['modelo']}</td>"
    f"<td style='font-family:Barlow Condensed;color:{SR_RED};font-weight:700'>{d['pin']}</td>"
    f"<td style='font-size:.78rem;color:#6b7f8f'>{d['arquivo']}</td>"
    f"<td>{badge(d['tipo'])}</td>"
    f"<td style='font-family:Barlow Condensed;color:#6b7f8f'>{d['fonte']}</td>"
    f"<td style='text-align:right;font-family:Barlow Condensed'>{d['registros']:,}</td></tr>"
    for d in dados)
st.markdown(f'<table class="file-table"><thead><tr><th>Modelo</th><th>PIN</th>'
    f'<th>Arquivo</th><th>Tipo</th><th>Fonte</th><th style="text-align:right">Registros</th></tr></thead>'
    f'<tbody>{rows}</tbody></table>', unsafe_allow_html=True)

# ── SELEÇÃO ───────────────────────────────────────────────────────────────────
sec("03 · Configurar Comparação")
def rotulo(d):
    # O nome do arquivo (chave do agrupamento) e sempre unico e ja costuma
    # conter o modelo; garante que dois equipamentos nunca colidam no seletor.
    if d["pin"] and d["pin"] != "N/A":
        return f"{d['arquivo']}  ·  PIN {d['pin']}"
    return d["arquivo"]
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
abas = st.tabs(["📊 Visão Geral", "🗺 Mapa", "📍 Precisão GPS", "🎯 Raio do Sistema",
    "📶 Rede & Operadora", "🛰 Qualidade GPS", "🚗 Movimento", "🔋 Bateria", "⏱ Latência",
    "📋 Dados & Export", "💾 Histórico", "❓ Como Usar"])

with abas[0]: g.aba_visao_geral(resultados, df_ref, ref_nome, raios)
with abas[1]: g.aba_mapa(resultados, df_ref, ref_nome)
with abas[2]: g.aba_precisao(resultados, raios)
with abas[3]: g.aba_raio_sistema(resultados)
with abas[4]: g.aba_rede(resultados, df_ref, ref_nome, comparacao, dados)
with abas[5]: g.aba_qualidade_gps(df_ref, ref_nome, comparacao, dados)
with abas[6]: g.aba_movimento(df_ref, ref_nome, comparacao, dados)
with abas[7]: g.aba_bateria(df_ref, ref_nome, comparacao, dados)
with abas[8]: g.aba_latencia(df_ref, ref_nome, comparacao, dados)
with abas[11]: render_ajuda()

with abas[9]:
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

# ── ABA HISTÓRICO ─────────────────────────────────────────────────────────────
with abas[10]:
    sec("Histórico de Relatórios")
    if not hist.disponivel():
        st.info(
            "📂 O histórico permite **salvar** os arquivos de uma análise no Google Drive "
            "e **reabrir** depois, sem precisar enviá-los de novo — útil para compartilhar "
            "com a equipe.\n\n"
            "PEGADINHA DO MALANDRO... Função não disponível.")
          
    else:
        # Salvar a análise atual
        st.markdown("**💾 Salvar esta análise no histórico**")
        cS1, cS2 = st.columns(2)
        with cS1:
            projeto = st.text_input("Projeto", placeholder="Ex.: Homologação RI720 2026")
        with cS2:
            rota = st.text_input("Rota", placeholder="Ex.: Campinas → Sumaré")
        if st.button("💾  Salvar no histórico"):
            ab = st.session_state.get("arquivos_bytes_atuais") or {}
            if not ab:
                st.warning("Nenhum arquivo carregado para salvar.")
            elif not (projeto.strip() or rota.strip()):
                st.warning("Informe ao menos o nome do projeto ou da rota.")
            else:
                try:
                    with st.spinner("Enviando arquivos ao Google Drive..."):
                        hist.salvar(projeto, rota, ab)
                    st.success("Análise salva no histórico com sucesso.")
                except Exception as e:
                    st.error(f"Falha ao salvar: {e}")

        st.markdown("---")
        st.markdown("**📁 Abrir uma análise salva**")
        busca = st.text_input("Pesquisar por projeto ou rota", key="busca_hist")
        if st.button("🔄  Atualizar lista") or "hist_lista" not in st.session_state:
            try:
                st.session_state["hist_lista"] = hist.listar()
            except Exception as e:
                st.error(f"Falha ao listar: {e}")
                st.session_state["hist_lista"] = []
        itens = st.session_state.get("hist_lista", [])
        if busca.strip():
            b = busca.lower()
            itens = [it for it in itens
                     if b in it["projeto"].lower() or b in it["rota_pasta"].lower()]
        if not itens:
            st.caption("Nenhuma análise salva encontrada.")
        for it in itens:
            cI1, cI2 = st.columns([4, 1])
            with cI1:
                st.markdown(f"**{it['projeto']}** · {it['rota_pasta']}")
            with cI2:
                if st.button("Abrir", key=f"open_{it['pasta_id']}"):
                    try:
                        with st.spinner("Baixando arquivos do Drive..."):
                            arqs = hist.baixar_arquivos(it["pasta_id"])
                        st.session_state["hist_arquivos"] = arqs
                        st.session_state["hist_label"] = f"{it['projeto']} · {it['rota_pasta']}"
                        # Limpa resultados antigos para reprocessar com os novos arquivos
                        for k in ("resultados", "ref_df", "comparacao", "df_resumo"):
                            st.session_state.pop(k, None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Falha ao abrir: {e}")
