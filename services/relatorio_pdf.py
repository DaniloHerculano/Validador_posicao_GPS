"""
relatorio_pdf.py — Gera um relatório PDF com o visual da plataforma.

Monta um HTML estilizado (cores e layout Stoneridge, cards e tabelas iguais aos
do site) e converte para PDF com o weasyprint. Os gráficos são desenhados como
barras em HTML/CSS puro (sem depender de kaleido/navegador), para funcionar no
Streamlit Cloud apenas com as libs de sistema do weasyprint (ver packages.txt).
"""
import datetime as _dt
import pandas as pd

from services.config import SR_RED, SR_SLATE, PALETA
from services.analise import analisar_buffer_lifo


def _dtec(item):
    return item.get("df_tecnico", item.get("df")) if item else None


def _curto(nome):
    return nome.split("_GNSS")[0] if "_GNSS" in nome else nome


def _barras_html(pares, cor=SR_RED, unidade="", maxv=None):
    """Gera um mini gráfico de barras horizontais em HTML/CSS."""
    if not pares:
        return "<p class='vazio'>sem dados</p>"
    mx = maxv if maxv else max(v for _, v in pares) or 1
    linhas = []
    for rotulo, v in pares:
        pct = min(v / mx * 100, 100) if mx else 0
        linhas.append(
            f"<div class='bar-row'><span class='bar-lbl'>{rotulo}</span>"
            f"<span class='bar-track'><span class='bar-fill' style='width:{pct:.1f}%;"
            f"background:{cor}'></span></span>"
            f"<span class='bar-val'>{v:.1f}{unidade}</span></div>")
    return "".join(linhas)


def _card(titulo, valor, sub="", cor=SR_SLATE):
    return (f"<div class='card' style='border-top-color:{cor}'>"
            f"<div class='card-lbl'>{titulo}</div>"
            f"<div class='card-val'>{valor}</div>"
            f"<div class='card-sub'>{sub}</div></div>")


def _tabela_html(df, maxlin=30):
    if df is None or len(df) == 0:
        return "<p class='vazio'>sem dados</p>"
    df = df.head(maxlin)
    th = "".join(f"<th>{c}</th>" for c in df.columns)
    trs = []
    for _, row in df.iterrows():
        tds = "".join(f"<td>{row[c]}</td>" for c in df.columns)
        trs.append(f"<tr>{tds}</tr>")
    return f"<table class='tbl'><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"


def _css():
    return f"""
    @page {{ size: A4; margin: 1.4cm 1.2cm; @bottom-right {{ content: "Página " counter(page) " / " counter(pages); font-size: 8px; color: #9aa7b2; }} }}
    * {{ font-family: 'Helvetica Neue', Arial, sans-serif; box-sizing: border-box; }}
    body {{ color: #2c3946; font-size: 10px; margin: 0; }}
    .hero {{ background: {SR_SLATE}; color: #fff; padding: 18px 20px; border-radius: 10px; margin-bottom: 16px; }}
    .hero h1 {{ margin: 0; font-size: 22px; letter-spacing: .5px; }}
    .hero .sub {{ font-size: 11px; color: #c7d0d8; margin-top: 3px; }}
    .hero .meta {{ font-size: 9px; color: #9fb0bd; margin-top: 8px; }}
    h2 {{ color: {SR_RED}; font-size: 12px; text-transform: uppercase; letter-spacing: .12em;
         border-bottom: 2px solid #e5ebf1; padding-bottom: 5px; margin: 20px 0 10px; }}
    h3 {{ font-size: 11px; color: {SR_SLATE}; margin: 12px 0 6px; }}
    .cards {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }}
    .card {{ flex: 1; min-width: 120px; background: #f7f9fb; border: 1px solid #e5ebf1;
            border-top: 3px solid {SR_SLATE}; border-radius: 8px; padding: 9px 11px; }}
    .card-lbl {{ font-size: 8px; text-transform: uppercase; letter-spacing: .05em; color: #6b7f8f; }}
    .card-val {{ font-size: 17px; font-weight: 700; color: {SR_SLATE}; margin: 2px 0; }}
    .card-sub {{ font-size: 8px; color: #8a99a6; }}
    .tbl {{ width: 100%; border-collapse: collapse; margin: 6px 0 12px; font-size: 9px; }}
    .tbl th {{ background: {SR_SLATE}; color: #fff; padding: 5px 7px; text-align: left; }}
    .tbl td {{ padding: 4px 7px; border-bottom: 1px solid #eef2f6; }}
    .tbl tbody tr:nth-child(even) {{ background: #f7f9fb; }}
    .bar-row {{ display: flex; align-items: center; gap: 6px; margin: 3px 0; }}
    .bar-lbl {{ width: 90px; font-size: 9px; color: #41535f; text-align: right; }}
    .bar-track {{ flex: 1; height: 13px; background: #eef2f6; border-radius: 3px; overflow: hidden; }}
    .bar-fill {{ display: block; height: 100%; }}
    .bar-val {{ width: 52px; font-size: 9px; color: #41535f; }}
    .vazio {{ color: #9aa7b2; font-style: italic; font-size: 9px; }}
    .note {{ background: #eef4fb; border-left: 3px solid #2477b3; padding: 7px 10px;
            font-size: 9px; color: #33475b; border-radius: 5px; margin: 6px 0; }}
    .sec {{ page-break-inside: avoid; }}
    """


def gerar_pdf(resultados, dados, raios, ref_nome="", eh_individual=False,
              tolerancia=10, tol_fusao=60) -> bytes:
    raio1, raio2, raio3 = raios
    H = []
    H.append(f"<div class='hero'><h1>TESTE DE RODAGEM</h1>"
             f"<div class='sub'>Análise comparativa GPS Real × Posição Estimada · Stoneridge Brasil</div>"
             f"<div class='meta'>Gerado em {_dt.datetime.now().strftime('%d/%m/%Y %H:%M')} · "
             f"Modo: {'Individual' if eh_individual else 'Comparativo'}"
             f"{(' · Referência: ' + _curto(ref_nome)) if ref_nome else ''}</div></div>")

    # ── Panorama ──
    total_reg = sum(d.get("registros", 0) for d in dados)
    tipos = [d.get("tipo", "—") for d in dados]
    n_est = sum(1 for t in tipos if "Estimada" in t)
    n_real = sum(1 for t in tipos if t == "GPS Real")
    n_misto = sum(1 for t in tipos if "Misto" in t)
    erros = pd.concat([df["distancia_km"].dropna() for df in resultados.values()
                       if len(df)], ignore_index=True) if resultados else pd.Series(dtype=float)
    erro_global = erros.mean() if len(erros) else None

    H.append("<div class='sec'><h2>Panorama do Teste</h2><div class='cards'>")
    H.append(_card("Equipamentos", f"{len(dados)}", "", "#2477b3"))
    H.append(_card("Registros totais", f"{total_reg:,}"))
    H.append(_card("Estimada / Real / Misto", f"{n_est} / {n_real} / {n_misto}"))
    if not eh_individual:
        H.append(_card("Erro médio global",
                       f"{erro_global:.3f} km" if erro_global is not None else "—",
                       "", "#1f8b4c" if (erro_global or 9) < raio2 else SR_RED))
    H.append("</div></div>")

    # ── Equipamentos ──
    df_eq = pd.DataFrame([{
        "Modelo": d.get("modelo", "—"), "PIN": d.get("pin", "—"),
        "Tipo": d.get("tipo", "—"), "Fonte": d.get("fonte", "—"),
        "Registros": d.get("registros", 0)} for d in dados])
    H.append(f"<div class='sec'><h2>Equipamentos</h2>{_tabela_html(df_eq)}</div>")

    # ── Precisão (modo comparativo) ──
    if not eh_individual and resultados:
        linhas = []
        for nome, df in resultados.items():
            d = df["distancia_km"].dropna()
            if len(d) == 0:
                continue
            lin = {"Equipamento": _curto(nome), "Sinc.": len(d),
                   f"% ≤{raio1}km": f"{(d <= raio1).mean()*100:.1f}",
                   f"% ≤{raio2}km": f"{(d <= raio2).mean()*100:.1f}",
                   f"% ≤{raio3}km": f"{(d <= raio3).mean()*100:.1f}",
                   "Erro Méd (km)": f"{d.mean():.3f}", "Erro Máx (km)": f"{d.max():.3f}"}
            if "dentro_raio" in df.columns:
                val = df.dropna(subset=["dentro_raio"])
                if len(val):
                    lin["% no Raio Sist."] = f"{val['dentro_raio'].mean()*100:.1f}"
            linhas.append(lin)
        if linhas:
            H.append("<div class='sec'><h2>Precisão de Posição</h2>")
            H.append(_tabela_html(pd.DataFrame(linhas)))
            # Barras de erro médio
            pares = [(_curto(n), df["distancia_km"].dropna().mean())
                     for n, df in resultados.items() if len(df["distancia_km"].dropna())]
            H.append("<h3>Erro médio por equipamento (km)</h3>")
            H.append(_barras_html(pares, cor=SR_RED, unidade=" km"))
            H.append("</div>")

    # ── Destaques por área (rede, bateria, latência/buffer) ──
    linhas_area = []
    for d in dados:
        dtec = _dtec(d)
        if dtec is None or len(dtec) == 0:
            continue
        reg = {"Equipamento": _curto(d.get("arquivo", "—"))}
        if "_tech" in dtec.columns and dtec["_tech"].notna().any():
            reg["Rede"] = dtec["_tech"].mode().iloc[0]
        if "_operadora" in dtec.columns and dtec["_operadora"].notna().any():
            reg["Operadora"] = dtec["_operadora"].mode().iloc[0]
        if "_banda" in dtec.columns and (dtec["_banda"] != "—").any():
            b = dtec[dtec["_banda"] != "—"]["_banda"].mode()
            reg["Banda"] = b.iloc[0] if len(b) else "—"
        bcol = "_bateria_pct" if "_bateria_pct" in dtec.columns else "_bateria_pct_csv"
        if bcol in dtec.columns and dtec[bcol].notna().any():
            bp = dtec[bcol].dropna()
            reg["Bateria"] = f"{bp.iloc[0]:.0f}%→{bp.iloc[-1]:.0f}%"
        if "_latencia_s" in dtec.columns and dtec["_latencia_s"].notna().any():
            bufm = dtec["_buffer_bool"].fillna(False) if "_buffer_bool" in dtec.columns \
                else pd.Series(False, index=dtec.index)
            lat_real = dtec[~bufm]["_latencia_s"].dropna()
            reg["Latência real"] = f"{lat_real.mean():.1f}s" if len(lat_real) else "—"
            reg["Buffer"] = f"{int(bufm.sum())} ({bufm.mean()*100:.0f}%)" if bufm.any() else "—"
        linhas_area.append(reg)
    if linhas_area:
        H.append(f"<div class='sec'><h2>Destaques por Área</h2>"
                 f"{_tabela_html(pd.DataFrame(linhas_area))}"
                 f"<div class='note'>Latência real considera apenas registros não "
                 f"bufferizados. O buffer indica registros que subiram atrasados após "
                 f"perda de sinal (não é lentidão de rede).</div></div>")

    html = f"<html><head><meta charset='utf-8'><style>{_css()}</style></head><body>{''.join(H)}</body></html>"

    from weasyprint import HTML
    return HTML(string=html).write_pdf()
