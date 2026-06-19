"""
graficos.py — Funções de renderização de cada aba de análise.
Cada função recebe os DataFrames e desenha métricas + gráficos via Streamlit.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from services.config import (
    SR_RED, SR_RED2, SR_SLATE, SR_LIGHT, COLORS_TECH, COLORS_RAIOS, PALETA,
    LATENCIA_BINS, LATENCIA_LABELS, LATENCIA_CORES,
)
from services.ui import tile, grid, sec, aplica_tema
import streamlit as st


# ══════════════════════════════════════════════════════════════════════════════
# VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
def aba_visao_geral(resultados, df_ref, ref_nome, raios):
    raio1, raio2, raio3 = raios
    sec("Resumo Comparativo")

    linhas = []
    for nome, df in resultados.items():
        if len(df) == 0:
            continue
        d = df["distancia_km"].dropna()
        if len(d) == 0:
            continue
        linha = {
            "Equipamento": nome, "Sincronizações": len(d),
            f"% ≤{raio1:.1f}km": round((d <= raio1).mean() * 100, 1),
            f"% ≤{raio2:.1f}km": round((d <= raio2).mean() * 100, 1),
            f"% ≤{raio3:.1f}km": round((d <= raio3).mean() * 100, 1),
            "Erro Médio (km)": round(d.mean(), 3),
            "Erro Máx (km)": round(d.max(), 3),
            "Erro Mín (km)": round(d.min(), 3),
            "Mediana (km)": round(d.median(), 3),
        }
        if "dentro_raio" in df.columns:
            val = df.dropna(subset=["dentro_raio"])
            if len(val) > 0:
                linha["% no Raio do Sistema"] = round(val["dentro_raio"].mean() * 100, 1)
        linhas.append(linha)

    df_resumo = pd.DataFrame(linhas) if linhas else None
    if df_resumo is not None:
        st.dataframe(df_resumo, use_container_width=True, hide_index=True)
        st.session_state["df_resumo"] = df_resumo

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            for i, r in enumerate(linhas):
                fig.add_trace(go.Bar(
                    name=r["Equipamento"],
                    x=[f"≤{raio1}km", f"≤{raio2}km", f"≤{raio3}km"],
                    y=[r[f"% ≤{raio1:.1f}km"], r[f"% ≤{raio2:.1f}km"], r[f"% ≤{raio3:.1f}km"]],
                    marker_color=PALETA[i % len(PALETA)]))
            fig.update_layout(title="% Dentro de Cada Raio", barmode="group")
            st.plotly_chart(aplica_tema(fig, 340), use_container_width=True, key="vg_raios")
        with c2:
            fig = go.Figure(go.Bar(
                x=[r["Equipamento"] for r in linhas],
                y=[r["Erro Médio (km)"] for r in linhas],
                marker_color=[PALETA[i % len(PALETA)] for i in range(len(linhas))],
                text=[f"{r['Erro Médio (km)']:.2f}" for r in linhas], textposition="outside"))
            fig.update_layout(title="Erro Médio por Equipamento (km)", showlegend=False)
            st.plotly_chart(aplica_tema(fig, 340), use_container_width=True, key="vg_erro")

    sec(f"Referência — {ref_nome}")
    gps_ok = int(df_ref["_gps_bool"].sum()) if "_gps_bool" in df_ref.columns else 0
    gps_tot = len(df_ref)
    bp = df_ref["_bateria_pct"].dropna() if "_bateria_pct" in df_ref.columns else pd.Series(dtype=float)
    bat_i = bp.iloc[0] if len(bp) else None
    bat_f = bp.iloc[-1] if len(bp) else None
    tot_sync = sum(len(df) for df in resultados.values())
    grid(
        tile("Registros Ref.", f"{gps_tot:,}", cc="blue"),
        tile("GPS Válido", f"{gps_ok:,}", f"{gps_ok/gps_tot*100:.1f}%" if gps_tot else "", "green"),
        tile("Total Sincronizado", f"{tot_sync:,}", f"{len(resultados)} equip."),
        tile("Bateria Ref.", f"{bat_i:.0f}%→{bat_f:.0f}%" if bat_i is not None else "N/A", cc="amber"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAPA
# ══════════════════════════════════════════════════════════════════════════════
def _circulo_geo(lat, lon, raio_km, n=40):
    """Gera os pontos (lat, lon) de um circulo de raio em km ao redor de um centro.
    Aproximacao adequada para escalas urbanas/regionais."""
    import math
    pts_lat, pts_lon = [], []
    dlat = raio_km / 111.32
    dlon = raio_km / (111.32 * max(math.cos(math.radians(lat)), 1e-6))
    for k in range(n + 1):
        ang = 2 * math.pi * k / n
        pts_lat.append(lat + dlat * math.sin(ang))
        pts_lon.append(lon + dlon * math.cos(ang))
    return pts_lat, pts_lon


def aba_mapa(resultados, df_ref, ref_nome):
    sec("Mapa Comparativo de Posições")
    st.caption("Referência (GPS Real) + amostras testadas · "
               "linhas = erro entre pontos sincronizados · passe o mouse para ver erro, posição e horário")

    if not {"latitude", "longitude"}.issubset(df_ref.columns):
        st.info("📄 O mapa precisa de posição (latitude/longitude), que vem do **XLS** "
                "(relatório de posição). Suba o XLS da referência para visualizar o mapa.")
        return

    # Controles gerais
    c1, c2 = st.columns([1, 1])
    with c1:
        mostrar = st.checkbox("Mostrar linhas de erro", value=True)
    with c2:
        formato = st.selectbox(
            "Formato dos marcadores das amostras",
            ["circle", "marker", "square", "diamond", "triangle"],
            format_func=lambda s: {
                "circle": "● Círculo", "marker": "📍 Pino", "square": "■ Quadrado",
                "diamond": "◆ Losango", "triangle": "▲ Triângulo"}.get(s, s),
            help="A referência sempre usa círculo azul. Se um formato não aparecer, escolha outro."
        )

    # Quais equipamentos têm raio do sistema (KML) disponível
    com_raio = [nome for nome, dfs in resultados.items()
                if len(dfs) > 0 and "raio_km" in dfs.columns
                and dfs["raio_km"].notna().any()]
    raio_ativo = {}
    destacar_fora = False
    if com_raio:
        st.markdown("**🎯 Raio do sistema (círculo de estimativa) — habilite por equipamento:**")
        cols = st.columns(min(len(com_raio), 4))
        for j, nome in enumerate(com_raio):
            with cols[j % len(cols)]:
                raio_ativo[nome] = st.checkbox(nome, value=False, key=f"raio_map_{j}")
        destacar_fora = st.checkbox(
            "Destacar em vermelho as amostras que ficaram fora do raio do sistema",
            value=False, key="destaca_fora")

    fig = go.Figure()

    # Referência
    df_ref_v = df_ref.dropna(subset=["latitude", "longitude"])
    ref_dt = (df_ref_v["datetime_module"].dt.strftime("%d/%m/%Y %H:%M:%S")
              if "datetime_module" in df_ref_v.columns else pd.Series([""] * len(df_ref_v)))
    fig.add_trace(go.Scattermap(
        lat=df_ref_v["latitude"], lon=df_ref_v["longitude"], mode="markers",
        marker=dict(size=8, color="#2477b3", symbol="circle"),
        name=f"REF · {ref_nome}",
        customdata=list(ref_dt),
        hovertemplate="<b>Referência (GPS Real)</b><br>"
                      "%{lat:.5f}, %{lon:.5f}<br>%{customdata}<extra></extra>"))

    # Amostras testadas
    for i, (nome, dfs) in enumerate(resultados.items()):
        if len(dfs) == 0 or not {"lat_comp", "lon_comp"}.issubset(dfs.columns):
            continue
        cor = PALETA[(i + 1) % len(PALETA)]
        dfv = dfs.dropna(subset=["lat_comp", "lon_comp"]).copy()
        if len(dfv) == 0:
            continue
        # data/hora da amostra
        if "horario_comp" in dfv.columns:
            dt_txt = pd.to_datetime(dfv["horario_comp"]).dt.strftime("%d/%m/%Y %H:%M:%S")
        else:
            dt_txt = pd.Series([""] * len(dfv), index=dfv.index)
        erro_txt = [f"{d:.3f} km" if pd.notna(d) else "—" for d in dfv["distancia_km"]]
        customdata = list(zip(erro_txt, list(dt_txt)))

        tem_raio_eq = "raio_km" in dfv.columns and dfv["raio_km"].notna().any()
        if destacar_fora and tem_raio_eq and "dentro_raio" in dfv.columns:
            base_idx = dfv.index
            dentro_mask = dfv["dentro_raio"].astype("boolean").fillna(True)
            cd = list(customdata)
            # Pontos dentro do raio (cor normal)
            din = dfv[dentro_mask.values]
            if len(din) > 0:
                cd_in = [cd[k] for k in range(len(dfv)) if bool(dentro_mask.values[k])]
                fig.add_trace(go.Scattermap(
                    lat=din["lat_comp"], lon=din["lon_comp"], mode="markers",
                    marker=dict(size=11, color=cor, symbol=formato),
                    name=nome, customdata=cd_in,
                    hovertemplate="<b>" + nome + "</b> (dentro do raio)<br>"
                                  "Erro: %{customdata[0]}<br>%{lat:.5f}, %{lon:.5f}<br>"
                                  "%{customdata[1]}<extra></extra>"))
            # Pontos fora do raio (vermelho destacado)
            dfora = dfv[~dentro_mask.values]
            if len(dfora) > 0:
                cd_out = [cd[k] for k in range(len(dfv)) if not bool(dentro_mask.values[k])]
                fig.add_trace(go.Scattermap(
                    lat=dfora["lat_comp"], lon=dfora["lon_comp"], mode="markers",
                    marker=dict(size=13, color="#d92020", symbol=formato),
                    name=f"{nome} — fora do raio", customdata=cd_out,
                    hovertemplate="<b>" + nome + "</b> ⚠ FORA do raio<br>"
                                  "Erro: %{customdata[0]}<br>%{lat:.5f}, %{lon:.5f}<br>"
                                  "%{customdata[1]}<extra></extra>"))
        else:
            fig.add_trace(go.Scattermap(
                lat=dfv["lat_comp"], lon=dfv["lon_comp"], mode="markers",
                marker=dict(size=11, color=cor, symbol=formato),
                name=nome,
                customdata=customdata,
                hovertemplate="<b>" + nome + "</b><br>"
                              "Erro: %{customdata[0]}<br>"
                              "%{lat:.5f}, %{lon:.5f}<br>"
                              "%{customdata[1]}<extra></extra>"))
        if mostrar:
            lats, lons = [], []
            for _, r in dfv.iterrows():
                lats += [r["lat_ref"], r["lat_comp"], None]
                lons += [r["lon_ref"], r["lon_comp"], None]
            fig.add_trace(go.Scattermap(
                lat=lats, lon=lons, mode="lines", line=dict(width=1, color=cor),
                opacity=0.35, name=f"erro {nome}", showlegend=False, hoverinfo="skip"))

        # Círculos de raio do sistema (se habilitado para este equipamento)
        if raio_ativo.get(nome) and "raio_km" in dfv.columns:
            dfr = dfv.dropna(subset=["raio_km"])
            clats, clons = [], []
            for _, r in dfr.iterrows():
                cl, co = _circulo_geo(r["lat_comp"], r["lon_comp"], r["raio_km"])
                clats += cl + [None]
                clons += co + [None]
            if clats:
                fig.add_trace(go.Scattermap(
                    lat=clats, lon=clons, mode="lines",
                    line=dict(width=1.2, color=cor), opacity=0.5,
                    name=f"raio {nome}", showlegend=True, hoverinfo="skip"))

    clat = df_ref_v["latitude"].mean() if len(df_ref_v) else -15.7
    clon = df_ref_v["longitude"].mean() if len(df_ref_v) else -47.9
    fig.update_layout(
        map=dict(style="carto-positron", center=dict(lat=clat, lon=clon), zoom=11),
        margin=dict(l=0, r=0, t=48, b=0), height=580, paper_bgcolor="#ffffff",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(255,255,255,.9)", bordercolor="#dce4ee", borderwidth=1,
                    font=dict(color="#1f2a36", size=11)),
        font=dict(family="Barlow, sans-serif", color="#1f2a36"))
    st.plotly_chart(fig, use_container_width=True, key="mapa_principal",
                    config={"modeBarButtonsToRemove": ["lasso2d", "select2d"]})

    pts = []
    for nome, dfs in resultados.items():
        if len(dfs) == 0 or not {"lat_comp", "lon_comp", "distancia_km"}.issubset(dfs.columns):
            continue
        dd = dfs.dropna(subset=["lat_comp", "lon_comp", "distancia_km"])
        for _, r in dd.iterrows():
            pts.append({"lat": r["lat_comp"], "lon": r["lon_comp"], "erro": r["distancia_km"]})
    if pts:
        sec("Mapa de Calor — Concentração de Erros")
        dfh = pd.DataFrame(pts)
        figh = px.density_map(dfh, lat="lat", lon="lon", z="erro", radius=20,
            center=dict(lat=clat, lon=clon), zoom=10, map_style="carto-positron",
            color_continuous_scale=["#1f8b4c", "#e08a1e", "#dd0933"])
        figh.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=480,
            paper_bgcolor="#ffffff", font=dict(family="Barlow, sans-serif", color="#1f2a36"))
        st.plotly_chart(figh, use_container_width=True, key="mapa_calor")


# ══════════════════════════════════════════════════════════════════════════════
# PRECISÃO GPS
# ══════════════════════════════════════════════════════════════════════════════
def aba_precisao(resultados, raios):
    raio1, raio2, raio3 = raios
    for ci, (nome, df) in enumerate(resultados.items()):
        d = df["distancia_km"].dropna() if len(df) and "distancia_km" in df.columns else df.head(0)
        resumo = f" · erro médio {d.mean():.3f} km · ≤{raio2:.0f}km {(d<=raio2).mean()*100:.0f}%" if len(d) else " · sem sincronização"
        with st.expander(f"📍 Precisão — {nome}{resumo}", expanded=(ci == 0)):
            if len(df) == 0:
                st.warning("Nenhuma sincronização encontrada. Ajuste a tolerância de horário.")
                continue
            if len(d) == 0:
                st.warning("Distâncias não calculadas (verificar coordenadas).")
                continue
            p1, p2, p3 = (d <= raio1).mean()*100, (d <= raio2).mean()*100, (d <= raio3).mean()*100
            cm = "green" if d.mean() <= raio2 else ("amber" if d.mean() <= raio3 else "")
            grid(
                tile("Sincronizações", f"{len(d):,}", cc="blue"),
                tile("Erro Médio", f"{d.mean():.3f} km", cc=cm),
                tile("Mediana", f"{d.median():.3f} km"),
                tile("Erro Máximo", f"{d.max():.3f} km"),
                tile(f"≤{raio1:.1f}km", f"{p1:.1f}%", cc="green"),
                tile(f"≤{raio2:.1f}km", f"{p2:.1f}%", cc="amber"),
                tile(f"≤{raio3:.1f}km", f"{p3:.1f}%"),
            )
            cL, cR = st.columns(2)
            with cL:
                fig = px.histogram(df, x="distancia_km", nbins=40,
                    title="Distribuição de Erros (km)", color_discrete_sequence=[SR_RED])
                for raio, cor, lbl in [(raio1, "#1f8b4c", f"{raio1}km"),
                                       (raio2, "#e08a1e", f"{raio2}km"),
                                       (raio3, "#d92020", f"{raio3}km")]:
                    fig.add_vline(x=raio, line_dash="dash", line_color=cor, line_width=1.5,
                        annotation_text=lbl, annotation_font_color=cor, annotation_position="top right")
                st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"hist_{ci}")
            with cR:
                d1 = (d <= raio1).sum(); d2 = ((d > raio1) & (d <= raio2)).sum()
                d3 = ((d > raio2) & (d <= raio3)).sum(); d4 = (d > raio3).sum()
                fig = go.Figure(go.Pie(
                    labels=[f"≤{raio1}km", f"{raio1}–{raio2}km", f"{raio2}–{raio3}km", f">{raio3}km"],
                    values=[d1, d2, d3, d4], hole=0.55, marker=dict(colors=COLORS_RAIOS)))
                fig.update_layout(title="Distribuição por Raio")
                st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"pie_raio_{ci}")
            if "horario_comp" in df.columns:
                dfs = df.sort_values("horario_comp")
                fig = px.line(dfs, x="horario_comp", y="distancia_km",
                    title="Erro ao Longo do Tempo", color_discrete_sequence=[SR_SLATE], markers=True)
                fig.add_hrect(y0=0, y1=raio2, fillcolor="#1f8b4c", opacity=0.07, line_width=0)
                st.plotly_chart(aplica_tema(fig, 260), use_container_width=True, key=f"line_{ci}")
            if "endereco_comp" in df.columns and df["endereco_comp"].notna().any():
                piores = df.dropna(subset=["distancia_km"]).nlargest(5, "distancia_km")
                if len(piores) > 0 and piores["endereco_comp"].notna().any():
                    st.markdown("**📍 Pontos de maior erro (endereço estimado):**")
                    tab = piores[["horario_comp", "distancia_km", "endereco_comp"]].copy()
                    tab.columns = ["Horário", "Erro (km)", "Endereço Estimado"]
                    st.dataframe(tab, use_container_width=True, hide_index=True)
            with st.expander(f"Ver tabela completa ({len(df)} registros)"):
                st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# REDE & OPERADORA
# ══════════════════════════════════════════════════════════════════════════════
def _rede_um(df_raw, titulo, df_prec=None, kid="x", expandir=False):
    with st.expander(titulo, expanded=expandir):
        if "_tech" not in df_raw.columns:
            st.info("📄 Dados de rede vêm do **CSV** (log técnico). Suba o CSV deste equipamento para ver esta análise."); return
        total = len(df_raw)
        tech_counts = df_raw["_tech"].value_counts()
        op_counts = df_raw["_operadora"].value_counts()
        c4 = df_raw["_tech"].str.startswith("4G").sum()
        c3 = df_raw["_tech"].str.startswith("3G").sum()
        c2 = df_raw["_tech"].str.startswith("2G").sum()
        cn = (df_raw["_tech"] == "Sem Sinal").sum()
        rt = c4 + c3 + c2
        p4 = round(c4/rt*100, 1) if rt else 0
        p3 = round(c3/rt*100, 1) if rt else 0
        p2 = round(c2/rt*100, 1) if rt else 0
        pn = round(cn/total*100, 1) if total else 0
        grid(
            tile("4G", f"{c4:,}", f"{p4}%", "green"),
            tile("3G", f"{c3:,}", f"{p3}%", "amber"),
            tile("2G", f"{c2:,}", f"{p2}%"),
            tile("Sem Sinal", f"{cn:,}", f"{pn}%"),
        )
        c1, c2c = st.columns(2)
        with c1:
            fig = go.Figure(go.Pie(labels=tech_counts.index, values=tech_counts.values,
                hole=0.55, marker=dict(colors=COLORS_TECH)))
            fig.update_layout(title="Tecnologia de Rede (2G / 3G / 4G)")
            st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"pietech_{kid}")
        with c2c:
            cores = [SR_RED if o == "TIM" else SR_SLATE if o == "Claro"
                     else "#2477b3" if o == "Vivo" else "#9aa7b3" for o in op_counts.index]
            fig = go.Figure(go.Bar(x=op_counts.index, y=op_counts.values, marker_color=cores,
                text=op_counts.values, textposition="outside"))
            fig.update_layout(title="Registros por Operadora", showlegend=False)
            st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"barop_{kid}")
        tab = pd.DataFrame({"Tecnologia": tech_counts.index, "Registros": tech_counts.values,
            "%": (tech_counts.values/total*100).round(1)})
        st.dataframe(tab, use_container_width=True, hide_index=True)
        op_pct = (op_counts/total*100).round(1)
        grid(*[tile(k, f"{v}%", f"{op_counts[k]:,} reg.", "amber" if k == "Claro" else "")
               for k, v in op_pct.items()])
        if "transmissiontype" in df_raw.columns and df_raw["transmissiontype"].notna().any():
            tt = df_raw["transmissiontype"].value_counts()
            fig = go.Figure(go.Pie(labels=tt.index, values=tt.values, hole=0.55,
                marker=dict(colors=[SR_RED, "#2477b3", SR_SLATE][:len(tt)])))
            fig.update_layout(title="Tipo de Transmissão (UDP / SMS / outros)")
            st.plotly_chart(aplica_tema(fig, 260), use_container_width=True, key=f"pitt_{kid}")
        if "networktype" in df_raw.columns and df_raw["networktype"].notna().any():
            nt = df_raw["networktype"].value_counts()
            fig = go.Figure(go.Bar(x=nt.index, y=nt.values, marker_color=SR_RED,
                text=nt.values, textposition="outside"))
            fig.update_layout(title="Network Type (LTE / GSM / ...)", showlegend=False)
            st.plotly_chart(aplica_tema(fig, 240), use_container_width=True, key=f"bnt_{kid}")
        # Frequência por banda do modem (GSM850/900/1800/1900, LTE B3/B5/B7/B28...)
        if "_banda" in df_raw.columns and (df_raw["_banda"] != "—").any():
            st.markdown("**📡 Frequência / Banda do modem**")
            dfb = df_raw[df_raw["_banda"] != "—"]
            banda_counts = dfb["_banda"].value_counts()
            base_b = len(dfb)
            # cor por geração: LTE azul, GSM laranja, demais cinza
            cores_b = ["#2477b3" if b.startswith("LTE") else
                       "#e08a1e" if b.startswith("GSM") else "#7c5cd0"
                       for b in banda_counts.index]
            fig = go.Figure(go.Bar(
                x=banda_counts.index, y=banda_counts.values, marker_color=cores_b,
                text=[f"{v}<br>{v/base_b*100:.1f}%" for v in banda_counts.values],
                textposition="outside"))
            fig.update_layout(title="Registros por Banda de Frequência", showlegend=False)
            st.plotly_chart(aplica_tema(fig, 280), use_container_width=True, key=f"bband_{kid}")
            tabb = pd.DataFrame({
                "Banda": banda_counts.index, "Registros": banda_counts.values,
                "%": (banda_counts.values / base_b * 100).round(1)})
            st.dataframe(tabb, use_container_width=True, hide_index=True)
        if df_prec is not None and "_tech_comp" in df_prec.columns and len(df_prec) > 0:
            dfb = df_prec[["_tech_comp", "distancia_km"]].dropna()
            if len(dfb) > 0:
                fig = px.box(dfb, x="_tech_comp", y="distancia_km",
                    title="Erro de Posição × Tecnologia de Rede", color="_tech_comp",
                    color_discrete_sequence=COLORS_TECH)
                st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"box_{kid}")


def aba_rede(resultados, df_ref, ref_nome, comparacao, dados):
    _rede_um(df_ref, f"Referência — {ref_nome}", kid="ref", expandir=True)
    for ci, nome in enumerate(comparacao):
        item = next((d for d in dados if d["arquivo"] == nome), None)
        if item:
            _rede_um(item["df"], nome, df_prec=resultados.get(nome), kid=f"c{ci}")


# ══════════════════════════════════════════════════════════════════════════════
# QUALIDADE GPS
# ══════════════════════════════════════════════════════════════════════════════
def _gps_um(df_raw, titulo, kid="x", expandir=False):
    with st.expander(titulo, expanded=expandir):
        tem_sat = "satellitenumber" in df_raw.columns and df_raw["satellitenumber"].notna().any()
        tem_dop = any(c in df_raw.columns and df_raw[c].notna().any() for c in ["hdop", "vdop", "sdop"])
        if not tem_sat and not tem_dop:
            st.info("📄 Satélites e DOP vêm do **CSV** (log técnico). Suba o CSV deste equipamento para ver esta análise."); return
        if tem_sat:
            sat = df_raw["satellitenumber"].dropna()
            grid(
                tile("Satélites Médio", f"{sat.mean():.1f}", cc="green"),
                tile("Satélites Máx", f"{int(sat.max())}"),
                tile("Satélites Mín", f"{int(sat.min())}", cc="amber"),
                tile("Registros", f"{len(sat):,}", cc="blue"),
            )
            c1, c2 = st.columns(2)
            with c1:
                fig = px.histogram(df_raw, x="satellitenumber", nbins=20,
                    title="Distribuição de Satélites", color_discrete_sequence=[SR_RED])
                st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"sathist_{kid}")
            with c2:
                if "datetime_module" in df_raw.columns:
                    dfs = df_raw.dropna(subset=["satellitenumber", "datetime_module"]).sort_values("datetime_module")
                    fig = px.line(dfs, x="datetime_module", y="satellitenumber",
                        title="Satélites ao Longo do Tempo", color_discrete_sequence=["#2477b3"])
                    st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"satline_{kid}")
        if tem_dop and "datetime_module" in df_raw.columns:
            fig = go.Figure()
            for col, cor in [("hdop", SR_RED), ("vdop", "#2477b3"), ("sdop", "#f59e0b")]:
                if col in df_raw.columns and df_raw[col].notna().any():
                    dfs = df_raw.dropna(subset=[col, "datetime_module"]).sort_values("datetime_module")
                    fig.add_trace(go.Scatter(x=dfs["datetime_module"], y=dfs[col],
                        mode="lines", name=col.upper(), line=dict(color=cor)))
            fig.update_layout(title="Diluição de Precisão (DOP) — menor é melhor")
            st.plotly_chart(aplica_tema(fig, 280), use_container_width=True, key=f"dop_{kid}")
        if "altitude" in df_raw.columns and df_raw["altitude"].notna().any() and "datetime_module" in df_raw.columns:
            dfs = df_raw.dropna(subset=["altitude", "datetime_module"]).sort_values("datetime_module")
            fig = px.area(dfs, x="datetime_module", y="altitude", title="Altitude (m)",
                color_discrete_sequence=[SR_SLATE])
            fig.update_traces(line_color=SR_SLATE)
            st.plotly_chart(aplica_tema(fig, 240), use_container_width=True, key=f"alt_{kid}")


def aba_qualidade_gps(df_ref, ref_nome, comparacao, dados):
    _gps_um(df_ref, f"Referência — {ref_nome}", kid="ref", expandir=True)
    for ci, nome in enumerate(comparacao):
        item = next((d for d in dados if d["arquivo"] == nome), None)
        if item:
            _gps_um(item["df"], nome, kid=f"c{ci}")


# ══════════════════════════════════════════════════════════════════════════════
# MOVIMENTO
# ══════════════════════════════════════════════════════════════════════════════
def _mov_um(df_raw, titulo, kid="x", expandir=False):
    with st.expander(titulo, expanded=expandir):
        tem_spd = "speed" in df_raw.columns and df_raw["speed"].notna().any()
        if not tem_spd and "_movimento" not in df_raw.columns:
            st.info("📄 Velocidade/direção vêm do **CSV** (log técnico) ou do XLS. Suba o CSV para a análise completa."); return
        if tem_spd:
            spd = df_raw["speed"].dropna()
            parado = (spd == 0).mean() * 100
            vmax = spd.max()
            vmed = spd[spd > 0].mean() if (spd > 0).any() else 0
            grid(
                tile("Vel. Máxima", f"{vmax:.0f} km/h", cc="amber"),
                tile("Vel. Média (mov.)", f"{vmed:.1f} km/h" if vmed == vmed else "0", cc="blue"),
                tile("% Parado", f"{parado:.1f}%", cc="green"),
                tile("Registros", f"{len(spd):,}"),
            )
            c1, c2 = st.columns(2)
            with c1:
                if "datetime_module" in df_raw.columns:
                    dfs = df_raw.dropna(subset=["speed", "datetime_module"]).sort_values("datetime_module")
                    fig = px.line(dfs, x="datetime_module", y="speed",
                        title="Velocidade ao Longo do Tempo (km/h)", color_discrete_sequence=[SR_RED])
                    st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"spd_{kid}")
            with c2:
                mov = spd[spd > 0]
                if len(mov) > 0:
                    fig = px.histogram(mov, nbins=25, title="Distribuição de Velocidade (em movimento)",
                        color_discrete_sequence=["#2477b3"])
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"spdhist_{kid}")
                else:
                    st.info("Equipamento permaneceu parado durante todo o período.")
        if "heading" in df_raw.columns and df_raw["heading"].notna().any():
            hd = df_raw["heading"].dropna()
            rotulos = ["N", "NE", "L", "SE", "S", "SO", "O", "NO"]
            bins = pd.cut(hd, bins=[0, 45, 90, 135, 180, 225, 270, 315, 360],
                labels=rotulos, include_lowest=True)
            hc = bins.value_counts().reindex(rotulos).fillna(0)
            fig = go.Figure(go.Barpolar(r=hc.values, theta=rotulos, marker_color=SR_RED))
            fig.update_layout(title="Rosa dos Ventos (direção/heading)",
                polar=dict(bgcolor="#f5f7fa", radialaxis=dict(color="#1f2a36"),
                    angularaxis=dict(color="#1f2a36")),
                paper_bgcolor="#ffffff", font=dict(family="Barlow", color="#1f2a36"), height=340)
            st.plotly_chart(fig, use_container_width=True, key=f"head_{kid}")
        if "_movimento" in df_raw.columns:
            mc = df_raw["_movimento"].value_counts()
            lbls = ["Em movimento" if i else "Parado" for i in mc.index]
            fig = go.Figure(go.Pie(labels=lbls, values=mc.values, hole=0.55,
                marker=dict(colors=["#1f8b4c", "#9aa7b3"])))
            fig.update_layout(title="Sensor de Movimento")
            st.plotly_chart(aplica_tema(fig, 260), use_container_width=True, key=f"movsens_{kid}")


def aba_movimento(df_ref, ref_nome, comparacao, dados):
    _mov_um(df_ref, f"Referência — {ref_nome}", kid="ref", expandir=True)
    for ci, nome in enumerate(comparacao):
        item = next((d for d in dados if d["arquivo"] == nome), None)
        if item:
            _mov_um(item["df"], nome, kid=f"c{ci}")


# ══════════════════════════════════════════════════════════════════════════════
# BATERIA
# ══════════════════════════════════════════════════════════════════════════════
def _bat_um(df_raw, titulo, kid="x", expandir=False):
    with st.expander(titulo, expanded=expandir):
        if "_bateria_pct" not in df_raw.columns or df_raw["_bateria_pct"].isna().all():
            st.info("📄 Bateria vem do **XLS** (em %) ou do CSV. Suba ao menos um deles para ver esta análise."); return
        dfb = df_raw.dropna(subset=["_bateria_pct", "datetime_module"]).sort_values("datetime_module")
        if len(dfb) == 0:
            st.info("Nenhum dado de bateria com timestamp válido."); return
        ini = dfb["_bateria_pct"].iloc[0]; fim = dfb["_bateria_pct"].iloc[-1]
        cons = ini - fim; media = dfb["_bateria_pct"].mean(); mn = dfb["_bateria_pct"].min()
        grid(
            tile("Bateria Início", f"{ini:.0f}%", cc="green"),
            tile("Bateria Fim", f"{fim:.0f}%", f"mín: {mn:.0f}%"),
            tile("Consumo", f"{cons:.0f}%", cc="amber" if cons > 20 else "green"),
            tile("Média", f"{media:.1f}%", cc="blue"),
        )
        fig = px.line(dfb, x="datetime_module", y="_bateria_pct",
            title="Nível de Bateria Interna (%)", color_discrete_sequence=[SR_RED])
        fig.add_hrect(y0=0, y1=20, fillcolor="#ef4444", opacity=0.1, line_width=0,
            annotation_text="Crítico (<20%)", annotation_font_color="#ef4444")
        fig.add_hrect(y0=20, y1=50, fillcolor="#f59e0b", opacity=0.07, line_width=0)
        fig.update_layout(yaxis=dict(range=[0, 105], title="Bateria (%)"))
        st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"bat_{kid}")
        if "voltage" in df_raw.columns and df_raw["voltage"].notna().any():
            dfv = df_raw.dropna(subset=["voltage", "datetime_module"]).sort_values("datetime_module")
            fig = px.line(dfv, x="datetime_module", y="voltage", title="Tensão (V)",
                color_discrete_sequence=["#2477b3"])
            st.plotly_chart(aplica_tema(fig, 240), use_container_width=True, key=f"volt_{kid}")


def aba_bateria(df_ref, ref_nome, comparacao, dados):
    _bat_um(df_ref, f"Referência — {ref_nome}", kid="ref", expandir=True)
    for ci, nome in enumerate(comparacao):
        item = next((d for d in dados if d["arquivo"] == nome), None)
        if item:
            _bat_um(item["df"], nome, kid=f"c{ci}")


# ══════════════════════════════════════════════════════════════════════════════
# LATÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
def _lat_um(df_raw, titulo, kid="x", expandir=False):
    with st.expander(titulo, expanded=expandir):
        if "_latencia_s" not in df_raw.columns or df_raw["_latencia_s"].isna().all():
            st.info("📄 Latência (módulo→servidor) vem do **CSV** (log técnico). Suba o CSV deste equipamento."); return
        dfl = df_raw.dropna(subset=["_latencia_s"])
        if len(dfl) == 0:
            st.info("Nenhum registro com latência válida."); return
        media = dfl["_latencia_s"].mean(); mx = dfl["_latencia_s"].max()
        pok = (dfl["_latencia_s"] <= 90).mean() * 100
        psms = 0
        if "transmissiontype" in df_raw.columns:
            psms = (df_raw["transmissiontype"].astype(str).str.upper() == "SMS").mean() * 100
        grid(
            tile("Latência Média", f"{media:.1f}s", cc="green" if media < 90 else "amber"),
            tile("Latência Máx", f"{mx:.0f}s"),
            tile("% ≤90s", f"{pok:.1f}%", cc="green"),
            tile("% SMS", f"{psms:.1f}%", cc="blue"),
        )
        dfl = dfl.copy()
        dfl["_cat"] = pd.cut(dfl["_latencia_s"], bins=LATENCIA_BINS, labels=LATENCIA_LABELS)
        cc = dfl["_cat"].value_counts().reindex(LATENCIA_LABELS).fillna(0)
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure(go.Bar(x=cc.index, y=cc.values, marker_color=LATENCIA_CORES,
                text=cc.values.astype(int), textposition="outside"))
            fig.update_layout(title="Distribuição de Latência por Faixa", showlegend=False)
            st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"lat_{kid}")
        with c2:
            if "bufferstatus" in df_raw.columns and df_raw["bufferstatus"].notna().any():
                buf = df_raw["bufferstatus"].astype(str).value_counts()
                lbls = ["Buffer (atrasado)" if v in ("t", "true", "1") else "Tempo real" for v in buf.index]
                fig = go.Figure(go.Pie(labels=lbls, values=buf.values, hole=0.55,
                    marker=dict(colors=[SR_RED, "#2477b3"])))
                fig.update_layout(title="Buffer Status")
                st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"buf_{kid}")
            else:
                st.info("Campo bufferstatus não disponível.")


def aba_latencia(df_ref, ref_nome, comparacao, dados):
    _lat_um(df_ref, f"Referência — {ref_nome}", kid="ref", expandir=True)
    for ci, nome in enumerate(comparacao):
        item = next((d for d in dados if d["arquivo"] == nome), None)
        if item:
            _lat_um(item["df"], nome, kid=f"c{ci}")

# ══════════════════════════════════════════════════════════════════════════════
def aba_raio_sistema(resultados):
    """Valida a distância medida contra o raio de incerteza do próprio sistema (KML)."""
    from services.analise import resumo_raio
    sec("Validação contra o Raio do Sistema (KML)")
    st.caption("Compara a distância medida (referência × amostra) com o raio de incerteza "
               "que o próprio sistema PST calcula para cada posição estimada. "
               "Indica o % de pontos em que a posição real caiu dentro do raio prometido pelo sistema.")

    algum = False
    for ci, (nome, df) in enumerate(resultados.items()):
        if len(df) == 0 or "dentro_raio" not in df.columns:
            continue
        rr = resumo_raio(df)
        if rr is None:
            continue
        algum = True
        cc = "green" if rr["pct_dentro"] >= 90 else ("amber" if rr["pct_dentro"] >= 70 else "")
        with st.expander(f"🎯 {nome} · {rr['pct_dentro']}% dentro do raio do sistema",
                         expanded=(ci == 0 or not algum)):
            grid(
                tile("Pontos avaliados", f"{rr['pontos']:,}", cc="blue"),
                tile("Dentro do raio", f"{rr['dentro']:,}", cc="green"),
                tile("% Dentro do raio", f"{rr['pct_dentro']}%", cc=cc),
                tile("Raio médio (sistema)", f"{rr['raio_medio']:.3f} km"),
                tile("Raio mín–máx", f"{rr['raio_min']:.2f}–{rr['raio_max']:.2f} km"),
            )
            val = df.dropna(subset=["dentro_raio", "distancia_km", "raio_km"]).copy()
            # Garantir tipo booleano limpo para somas e negação
            val["dentro_raio"] = val["dentro_raio"].astype(bool)
            if len(val) == 0:
                st.info("Sem pontos com raio do sistema para este equipamento.")
                continue

            cL, cR = st.columns(2)
            with cL:
                dentro = int(val["dentro_raio"].sum())
                fora = len(val) - dentro
                fig = go.Figure(go.Pie(
                    labels=["Dentro do raio", "Fora do raio"], values=[dentro, fora],
                    hole=0.55, marker=dict(colors=["#1f8b4c", SR_RED])))
                fig.update_layout(title="Posições dentro × fora do raio do sistema")
                st.plotly_chart(aplica_tema(fig), use_container_width=True, key=f"raio_pie_{ci}")
            with cR:
                # Distância medida vs raio do sistema, ao longo do tempo
                if "horario_comp" in val.columns:
                    vs = val.sort_values("horario_comp")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=vs["horario_comp"], y=vs["raio_km"],
                        name="Raio do sistema", mode="lines", line=dict(color="#2477b3", width=1.5),
                        fill="tozeroy", fillcolor="rgba(36,119,179,.12)"))
                    fig.add_trace(go.Scatter(x=vs["horario_comp"], y=vs["distancia_km"],
                        name="Distância medida", mode="markers",
                        marker=dict(size=5, color=SR_RED)))
                    fig.update_layout(title="Distância medida × Raio do sistema")
                    st.plotly_chart(aplica_tema(fig, 300), use_container_width=True, key=f"raio_ts_{ci}")

            st.markdown("**Pontos que ficaram fora do raio do sistema (maiores excedentes):**")
            fora_df = val[~val["dentro_raio"]].copy()
            if len(fora_df) > 0:
                fora_df["excedente_km"] = (fora_df["distancia_km"] - fora_df["raio_km"]).round(3)
                cols = [c for c in ["horario_comp", "distancia_km", "raio_km", "excedente_km", "endereco_comp"]
                        if c in fora_df.columns]
                tab = fora_df.nlargest(min(8, len(fora_df)), "excedente_km")[cols].copy()
                ren = {"horario_comp": "Horário", "distancia_km": "Distância (km)",
                       "raio_km": "Raio sistema (km)", "excedente_km": "Excedente (km)",
                       "endereco_comp": "Endereço estimado"}
                tab.columns = [ren.get(c, c) for c in tab.columns]
                st.dataframe(tab, use_container_width=True, hide_index=True)
            else:
                st.success("Todas as posições avaliadas ficaram dentro do raio do sistema.")

    if not algum:
        st.info("📄 Esta análise requer o arquivo **KML** (extraído do portal SSO/PST), que "
                "contém o raio de incerteza de cada posição estimada. Suba o KML dos "
                "equipamentos com posição estimada — junto do XLS de referência — para validar "
                "contra o raio do sistema. O KML deve ter o mesmo nome do CSV/XLS, mudando só a extensão.")
