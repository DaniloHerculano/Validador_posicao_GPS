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
        linhas.append({
            "Equipamento": nome, "Sincronizações": len(d),
            f"% ≤{raio1:.1f}km": round((d <= raio1).mean() * 100, 1),
            f"% ≤{raio2:.1f}km": round((d <= raio2).mean() * 100, 1),
            f"% ≤{raio3:.1f}km": round((d <= raio3).mean() * 100, 1),
            "Erro Médio (km)": round(d.mean(), 3),
            "Erro Máx (km)": round(d.max(), 3),
            "Erro Mín (km)": round(d.min(), 3),
            "Mediana (km)": round(d.median(), 3),
        })

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
def aba_mapa(resultados, df_ref, ref_nome):
    sec("Mapa Comparativo de Posições")
    st.caption("🔵 Referência (GPS Real) · pontos coloridos = comparados · "
               "linhas = erro entre pontos sincronizados")

    fig = go.Figure()
    df_ref_v = df_ref.dropna(subset=["latitude", "longitude"])
    fig.add_trace(go.Scattermapbox(
        lat=df_ref_v["latitude"], lon=df_ref_v["longitude"], mode="markers",
        marker=dict(size=7, color="#2477b3"), name=f"REF: {ref_nome}",
        text=df_ref_v.get("datetime_module", pd.Series()).astype(str),
        hovertemplate="<b>Referência</b><br>%{text}<br>%{lat:.5f}, %{lon:.5f}<extra></extra>"))

    mostrar = st.checkbox("Mostrar linhas de erro", value=True)

    for i, (nome, dfs) in enumerate(resultados.items()):
        if len(dfs) == 0:
            continue
        cor = PALETA[(i + 1) % len(PALETA)]
        dfv = dfs.dropna(subset=["lat_comp", "lon_comp"])
        fig.add_trace(go.Scattermapbox(
            lat=dfv["lat_comp"], lon=dfv["lon_comp"], mode="markers",
            marker=dict(size=8, color=cor), name=nome,
            text=[f"{d:.2f} km" if pd.notna(d) else "" for d in dfv["distancia_km"]],
            hovertemplate="<b>" + nome + "</b><br>Erro: %{text}<br>%{lat:.5f}, %{lon:.5f}<extra></extra>"))
        if mostrar:
            lats, lons = [], []
            for _, r in dfv.iterrows():
                lats += [r["lat_ref"], r["lat_comp"], None]
                lons += [r["lon_ref"], r["lon_comp"], None]
            fig.add_trace(go.Scattermapbox(
                lat=lats, lon=lons, mode="lines", line=dict(width=1, color=cor),
                opacity=0.35, name=f"erro {nome}", showlegend=False, hoverinfo="skip"))

    clat = df_ref_v["latitude"].mean() if len(df_ref_v) else -15.7
    clon = df_ref_v["longitude"].mean() if len(df_ref_v) else -47.9
    fig.update_layout(
        mapbox=dict(style="carto-positron", center=dict(lat=clat, lon=clon), zoom=11),
        margin=dict(l=0, r=0, t=0, b=0), height=560, paper_bgcolor="#ffffff",
        legend=dict(bgcolor="rgba(255,255,255,.85)", font=dict(color="#1f2a36")),
        font=dict(family="Barlow, sans-serif", color="#1f2a36"))
    st.plotly_chart(fig, use_container_width=True, key="mapa_principal")

    pts = []
    for nome, dfs in resultados.items():
        dd = dfs.dropna(subset=["lat_comp", "lon_comp", "distancia_km"])
        for _, r in dd.iterrows():
            pts.append({"lat": r["lat_comp"], "lon": r["lon_comp"], "erro": r["distancia_km"]})
    if pts:
        sec("Mapa de Calor — Concentração de Erros")
        dfh = pd.DataFrame(pts)
        figh = px.density_mapbox(dfh, lat="lat", lon="lon", z="erro", radius=20,
            center=dict(lat=clat, lon=clon), zoom=10, mapbox_style="carto-positron",
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
