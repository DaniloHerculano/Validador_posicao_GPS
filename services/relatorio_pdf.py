"""
relatorio_pdf.py — Relatório PDF com o visual da plataforma, usando fpdf2.

fpdf2 é "puro Python" (não exige bibliotecas de sistema como o weasyprint),
então instala limpo no Streamlit Cloud e não quebra o deploy. Reproduz o visual
Stoneridge: faixa (hero) escura, cards de KPI, tabelas e barras.
"""
import datetime as _dt
import pandas as pd
from fpdf import FPDF

# Cores (RGB)
SLATE = (44, 57, 70)
RED = (221, 9, 51)
GREEN = (31, 139, 76)
BLUE = (36, 119, 179)
AMBER = (224, 138, 30)
GREY = (107, 127, 143)
LIGHT = (243, 246, 250)
BORDER = (229, 235, 241)


def _dtec(item):
    return item.get("df_tecnico", item.get("df")) if item else None


def _curto(nome):
    return (nome.split("_GNSS")[0] if "_GNSS" in nome else nome)[:28]


def _txt(s):
    """Converte para latin-1 (fonte core do fpdf) de forma segura."""
    if s is None:
        return ""
    s = str(s)
    repl = {"≤": "<=", "→": "->", "×": "x", "·": "-", "–": "-", "—": "-",
            "ª": "a", "º": "o", "🏆": "", "⚠️": "", "🎯": "", "📡": "", "ℹ️": ""}
    for k, v in repl.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


class _PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*GREY)
        self.cell(0, 8, _txt(f"Teste de Rodagem - Stoneridge Brasil   |   Página {self.page_no()}"),
                  align="C")


def _hero(pdf, ref_nome, eh_individual):
    pdf.set_fill_color(*SLATE)
    pdf.rect(0, 0, 210, 32, "F")
    pdf.set_xy(12, 7)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, _txt("TESTE DE RODAGEM"))
    pdf.set_xy(12, 18)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(210, 220, 230)
    pdf.cell(0, 5, _txt("Análise comparativa GPS Real x Posição Estimada - Stoneridge Brasil"))
    pdf.set_xy(12, 24)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(160, 176, 189)
    meta = (f"Gerado em {_dt.datetime.now().strftime('%d/%m/%Y %H:%M')}  -  "
            f"Modo: {'Individual' if eh_individual else 'Comparativo'}")
    if ref_nome:
        meta += f"  -  Referência: {_curto(ref_nome)}"
    pdf.cell(0, 5, _txt(meta))
    pdf.set_y(38)


def _titulo(pdf, txt):
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*RED)
    pdf.cell(0, 7, _txt(txt.upper()), new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y()
    pdf.set_draw_color(*BORDER)
    pdf.line(12, y, 198, y)
    pdf.ln(2)
    pdf.set_text_color(*SLATE)


def _cards(pdf, cards):
    """cards: lista de (label, valor, sub, cor). Desenha em linha."""
    if not cards:
        return
    n = len(cards)
    gap = 4
    w = (186 - gap * (n - 1)) / n
    x0 = 12
    y0 = pdf.get_y()
    h = 20
    for i, (lbl, val, sub, cor) in enumerate(cards):
        x = x0 + i * (w + gap)
        pdf.set_fill_color(*LIGHT)
        pdf.set_draw_color(*BORDER)
        pdf.rect(x, y0, w, h, "DF")
        # barra de cor no topo
        pdf.set_fill_color(*cor)
        pdf.rect(x, y0, w, 1.6, "F")
        pdf.set_xy(x + 2, y0 + 3)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(*GREY)
        pdf.cell(w - 4, 3, _txt(lbl.upper()))
        pdf.set_xy(x + 2, y0 + 7)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*SLATE)
        pdf.cell(w - 4, 7, _txt(val))
        pdf.set_xy(x + 2, y0 + 14.5)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(130, 145, 158)
        pdf.cell(w - 4, 3, _txt(sub))
    pdf.set_y(y0 + h + 3)


def _tabela(pdf, df, larguras=None, maxlin=40):
    if df is None or len(df) == 0:
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*GREY)
        pdf.cell(0, 6, _txt("sem dados"), new_x="LMARGIN", new_y="NEXT")
        return
    df = df.head(maxlin)
    cols = list(df.columns)
    if larguras is None:
        larguras = [186 / len(cols)] * len(cols)
    # cabeçalho
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(*SLATE)
    pdf.set_text_color(255, 255, 255)
    for c, w in zip(cols, larguras):
        pdf.cell(w, 7, _txt(c), border=0, fill=True, align="L")
    pdf.ln()
    # linhas
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*SLATE)
    for idx, (_, row) in enumerate(df.iterrows()):
        if pdf.get_y() > 275:
            pdf.add_page()
        fill = idx % 2 == 1
        if fill:
            pdf.set_fill_color(*LIGHT)
        for c, w in zip(cols, larguras):
            pdf.cell(w, 6, _txt(row[c]), border="B", fill=fill, align="L")
        pdf.ln()
    pdf.set_draw_color(*BORDER)


def _barras(pdf, pares, unidade="", cor=RED):
    if not pares:
        return
    mx = max(v for _, v in pares) or 1
    pdf.set_font("Helvetica", "", 7.5)
    for rotulo, v in pares:
        if pdf.get_y() > 278:
            pdf.add_page()
        y = pdf.get_y()
        pdf.set_text_color(*SLATE)
        pdf.set_xy(12, y)
        pdf.cell(42, 5, _txt(_curto(rotulo)), align="R")
        # trilho
        bx, bw = 56, 110
        pdf.set_fill_color(*BORDER)
        pdf.rect(bx, y + 0.8, bw, 3.4, "F")
        # preenchimento
        pdf.set_fill_color(*cor)
        pdf.rect(bx, y + 0.8, bw * min(v / mx, 1), 3.4, "F")
        pdf.set_xy(bx + bw + 2, y)
        pdf.set_text_color(*GREY)
        pdf.cell(26, 5, _txt(f"{v:.2f}{unidade}"))
        pdf.ln(5.5)


def _nota(pdf, texto):
    pdf.ln(1)
    y = pdf.get_y()
    pdf.set_fill_color(238, 244, 251)
    pdf.set_draw_color(*BLUE)
    altura = 5 + 4 * (1 + len(texto) // 110)
    pdf.rect(12, y, 186, altura, "F")
    pdf.set_fill_color(*BLUE)
    pdf.rect(12, y, 1.5, altura, "F")
    pdf.set_xy(15, y + 1.5)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(51, 71, 91)
    pdf.multi_cell(180, 3.6, _txt(texto))
    pdf.set_y(y + altura + 2)


def _quebra(pdf, limite=235):
    if pdf.get_y() > limite:
        pdf.add_page()


def _melhor_peca(pdf, dados, resultados):
    """Cards: melhor peça em cada área."""
    cards = []
    if resultados:
        erro = {n: df["distancia_km"].dropna().mean() for n, df in resultados.items()
                if "distancia_km" in df.columns and len(df["distancia_km"].dropna())}
        if erro:
            mb = min(erro, key=erro.get)
            cards.append(("Melhor precisao", _curto(mb), f"erro {erro[mb]:.3f} km", GREEN))
        dr = {}
        for n, df in resultados.items():
            if "dentro_raio" in df.columns:
                v = df.dropna(subset=["dentro_raio"])
                if len(v):
                    dr[n] = v["dentro_raio"].mean() * 100
        if dr:
            mb = max(dr, key=dr.get)
            cards.append(("Melhor validacao raio", _curto(mb), f"{dr[mb]:.1f}% dentro", GREEN))
    raio_m, bat, gpsv, sat, lat, buf, r4g = {}, {}, {}, {}, {}, {}, {}
    for d in dados:
        dtec = _dtec(d)
        if dtec is None or len(dtec) == 0:
            continue
        nome = d.get("arquivo", "-")
        if "raio_km" in dtec.columns:
            rk = pd.to_numeric(dtec["raio_km"], errors="coerce").dropna()
            if len(rk):
                raio_m[nome] = rk.mean()
        bcol = "_bateria_pct" if "_bateria_pct" in dtec.columns else "_bateria_pct_csv"
        if bcol in dtec.columns and dtec[bcol].notna().any():
            bp = dtec[bcol].dropna()
            if len(bp) >= 2:
                bat[nome] = bp.iloc[0] - bp.iloc[-1]
        if "_gps_bool" in dtec.columns and dtec["_gps_bool"].notna().any():
            gpsv[nome] = dtec["_gps_bool"].mean() * 100
        if "satellitenumber" in dtec.columns and dtec["satellitenumber"].notna().any():
            sat[nome] = dtec["satellitenumber"].dropna().mean()
        if "_latencia_s" in dtec.columns and dtec["_latencia_s"].notna().any():
            bufm = dtec["_buffer_bool"].fillna(False) if "_buffer_bool" in dtec.columns else pd.Series(False, index=dtec.index)
            lr = dtec[~bufm]["_latencia_s"].dropna()
            if len(lr):
                lat[nome] = lr.mean()
            buf[nome] = bufm.mean() * 100
        if "_tech" in dtec.columns and dtec["_tech"].notna().any():
            r4g[nome] = dtec["_tech"].str.startswith("4G").mean() * 100
    if raio_m:
        mb = min(raio_m, key=raio_m.get)
        cards.append(("Menor raio do sistema", _curto(mb), f"raio {raio_m[mb]:.2f} km", GREEN))
    if bat:
        mb = min(bat, key=bat.get)
        cards.append(("Melhor bateria", _curto(mb), f"queda {bat[mb]:.0f}%", GREEN))
    if gpsv and max(gpsv.values()) > 0:
        mb = max(gpsv, key=gpsv.get)
        cards.append(("Melhor GPS", _curto(mb), f"{gpsv[mb]:.1f}% valido", GREEN))
    elif sat:
        mb = max(sat, key=sat.get)
        cards.append(("Melhor GPS", _curto(mb), f"{sat[mb]:.1f} satelites", GREEN))
    if r4g:
        mb = max(r4g, key=r4g.get)
        cards.append(("Melhor cobertura 4G", _curto(mb), f"{r4g[mb]:.1f}% em 4G", GREEN))
    if lat:
        mb = min(lat, key=lat.get)
        cards.append(("Menor latencia", _curto(mb), f"{lat[mb]:.1f}s", GREEN))
    if buf and max(buf.values()) > 0:
        mb = min(buf, key=buf.get)
        cards.append(("Menos buffer", _curto(mb), f"{buf[mb]:.1f}%", GREEN))
    if cards:
        _quebra(pdf, 215)
        _titulo(pdf, "Melhor Peca em Cada Area")
        # desenha em linhas de até 4 cards
        for i in range(0, len(cards), 4):
            _cards(pdf, cards[i:i+4])


def _comparacao_lado_a_lado(pdf, dados):
    """Tabela transposta: uma coluna por peça, uma linha por quesito."""
    cols = {}
    for d in dados:
        dtec = _dtec(d)
        if dtec is None or len(dtec) == 0:
            continue
        nome = _curto(d.get("arquivo", "-"))
        col = {"Modelo": d.get("modelo", "-"), "Tipo": d.get("tipo", "-"),
               "Registros": f"{d.get('registros', 0):,}"}
        if "_tech" in dtec.columns and dtec["_tech"].notna().any():
            col["Rede 4G"] = f"{dtec['_tech'].str.startswith('4G').mean()*100:.0f}%"
            col["Rede 2G"] = f"{dtec['_tech'].str.startswith('2G').mean()*100:.0f}%"
            col["Indefinido"] = f"{(dtec['_tech']=='Indefinido').mean()*100:.0f}%"
        if "_operadora" in dtec.columns and dtec["_operadora"].notna().any():
            col["Operadora"] = dtec["_operadora"].mode().iloc[0]
        if "_banda" in dtec.columns and (dtec["_banda"] != "-").any():
            b = dtec[dtec["_banda"] != "-"]["_banda"].mode()
            col["Banda"] = b.iloc[0] if len(b) else "-"
        bcol = "_bateria_pct" if "_bateria_pct" in dtec.columns else "_bateria_pct_csv"
        if bcol in dtec.columns and dtec[bcol].notna().any():
            bp = dtec[bcol].dropna()
            col["Bat. inicio"] = f"{bp.iloc[0]:.0f}%"
            col["Bat. fim"] = f"{bp.iloc[-1]:.0f}%"
            if len(bp) >= 2:
                col["Consumo"] = f"{bp.iloc[0]-bp.iloc[-1]:.0f}%"
        if "_gps_bool" in dtec.columns and dtec["_gps_bool"].notna().any():
            col["GPS valido"] = f"{dtec['_gps_bool'].mean()*100:.0f}%"
        if "satellitenumber" in dtec.columns and dtec["satellitenumber"].notna().any():
            col["Satelites"] = f"{dtec['satellitenumber'].dropna().mean():.1f}"
        if "raio_km" in dtec.columns:
            rk = pd.to_numeric(dtec["raio_km"], errors="coerce").dropna()
            if len(rk):
                col["Raio medio"] = f"{rk.mean():.2f} km"
        if "_latencia_s" in dtec.columns and dtec["_latencia_s"].notna().any():
            bufm = dtec["_buffer_bool"].fillna(False) if "_buffer_bool" in dtec.columns else pd.Series(False, index=dtec.index)
            lr = dtec[~bufm]["_latencia_s"].dropna()
            col["Latencia real"] = f"{lr.mean():.1f}s" if len(lr) else "-"
            col["Buffer"] = f"{bufm.mean()*100:.0f}%" if bufm.any() else "0%"
        cols[nome] = col
    if len(cols) < 2:
        return
    quesitos = []
    for col in cols.values():
        for k in col:
            if k not in quesitos:
                quesitos.append(k)
    # DataFrame: coluna "Quesito" + uma coluna por equipamento
    df = pd.DataFrame({"Quesito": quesitos})
    for nome, col in cols.items():
        df[nome] = [col.get(q, "-") for q in quesitos]
    _quebra(pdf, 200)
    _titulo(pdf, "Comparacao Lado a Lado")
    # largura: quesito fixo + resto dividido
    nc = len(cols)
    larg = [40] + [(186 - 40) / nc] * nc
    _tabela(pdf, df, larguras=larg, maxlin=40)


def gerar_pdf(resultados, dados, raios, ref_nome="", eh_individual=False,
              tolerancia=10, tol_fusao=60) -> bytes:
    raio1, raio2, raio3 = raios
    pdf = _PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(True, margin=15)
    pdf.set_margins(12, 12, 12)
    pdf.add_page()
    _hero(pdf, ref_nome, eh_individual)

    # ── Panorama ──
    total_reg = sum(d.get("registros", 0) for d in dados)
    tipos = [d.get("tipo", "-") for d in dados]
    n_est = sum(1 for t in tipos if "Estimada" in t)
    n_real = sum(1 for t in tipos if t == "GPS Real")
    n_misto = sum(1 for t in tipos if "Misto" in t)
    _se = [df["distancia_km"].dropna() for df in resultados.values()
           if len(df) and "distancia_km" in df.columns]
    erros = pd.concat(_se, ignore_index=True) if _se else pd.Series(dtype=float)
    erro_global = erros.mean() if len(erros) else None

    _titulo(pdf, "Panorama do Teste")
    cards = [("Equipamentos", str(len(dados)), "", BLUE),
             ("Registros totais", f"{total_reg:,}", "", SLATE),
             ("Est / Real / Misto", f"{n_est} / {n_real} / {n_misto}", "", SLATE)]
    if not eh_individual:
        cards.append(("Erro medio global",
                      f"{erro_global:.3f} km" if erro_global is not None else "-", "",
                      GREEN if (erro_global or 9) < raio2 else RED))
    _cards(pdf, cards)

    # ── Equipamentos ──
    _titulo(pdf, "Equipamentos")
    df_eq = pd.DataFrame([{
        "Modelo": d.get("modelo", "-"), "PIN": d.get("pin", "-"),
        "Tipo": d.get("tipo", "-"), "Fonte": d.get("fonte", "-"),
        "Registros": d.get("registros", 0)} for d in dados])
    _tabela(pdf, df_eq, larguras=[22, 28, 48, 48, 40])

    # ── Melhor peça em cada área + comparação lado a lado ──
    _melhor_peca(pdf, dados, resultados if not eh_individual else None)
    if len(dados) >= 2:
        _comparacao_lado_a_lado(pdf, dados)

    # ── Precisão (comparativo) ──
    if not eh_individual and resultados:
        linhas = []
        for nome, df in resultados.items():
            if "distancia_km" not in df.columns:
                continue
            d = df["distancia_km"].dropna()
            if len(d) == 0:
                continue
            lin = {"Equipamento": _curto(nome), "Sinc": len(d),
                   f"%<={raio1}km": f"{(d <= raio1).mean()*100:.1f}",
                   f"%<={raio2}km": f"{(d <= raio2).mean()*100:.1f}",
                   f"%<={raio3}km": f"{(d <= raio3).mean()*100:.1f}",
                   "Erro Med": f"{d.mean():.3f}", "Erro Max": f"{d.max():.3f}"}
            if "dentro_raio" in df.columns:
                val = df.dropna(subset=["dentro_raio"])
                if len(val):
                    lin["% Raio Sist"] = f"{val['dentro_raio'].mean()*100:.1f}"
            linhas.append(lin)
        if linhas:
            _titulo(pdf, "Precisão de Posição")
            dfp = pd.DataFrame(linhas)
            _tabela(pdf, dfp)
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*SLATE)
            pdf.cell(0, 5, _txt("Erro médio por equipamento (km)"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            pares = [(n, df["distancia_km"].dropna().mean())
                     for n, df in resultados.items()
                     if "distancia_km" in df.columns and len(df["distancia_km"].dropna())]
            _barras(pdf, pares, unidade=" km", cor=RED)

    # ── Destaques por área ──
    linhas_area = []
    for d in dados:
        dtec = _dtec(d)
        if dtec is None or len(dtec) == 0:
            continue
        reg = {"Equipamento": _curto(d.get("arquivo", "-"))}
        if "_tech" in dtec.columns and dtec["_tech"].notna().any():
            reg["Rede"] = dtec["_tech"].mode().iloc[0]
        if "_operadora" in dtec.columns and dtec["_operadora"].notna().any():
            reg["Operadora"] = dtec["_operadora"].mode().iloc[0]
        if "_banda" in dtec.columns and (dtec["_banda"] != "-").any():
            b = dtec[dtec["_banda"] != "-"]["_banda"].mode()
            reg["Banda"] = b.iloc[0] if len(b) else "-"
        bcol = "_bateria_pct" if "_bateria_pct" in dtec.columns else "_bateria_pct_csv"
        if bcol in dtec.columns and dtec[bcol].notna().any():
            bp = dtec[bcol].dropna()
            reg["Bateria"] = f"{bp.iloc[0]:.0f}%->{bp.iloc[-1]:.0f}%"
        if "_latencia_s" in dtec.columns and dtec["_latencia_s"].notna().any():
            bufm = dtec["_buffer_bool"].fillna(False) if "_buffer_bool" in dtec.columns \
                else pd.Series(False, index=dtec.index)
            lat_real = dtec[~bufm]["_latencia_s"].dropna()
            reg["Lat real"] = f"{lat_real.mean():.1f}s" if len(lat_real) else "-"
            reg["Buffer"] = f"{int(bufm.sum())} ({bufm.mean()*100:.0f}%)" if bufm.any() else "-"
        linhas_area.append(reg)
    if linhas_area:
        if pdf.get_y() > 230:
            pdf.add_page()
        _titulo(pdf, "Destaques por Área")
        _tabela(pdf, pd.DataFrame(linhas_area))
        _nota(pdf, "Latência real considera apenas registros não bufferizados. O buffer "
                   "indica registros que subiram atrasados após perda de sinal (não é "
                   "lentidão de rede).")

    # ── Distribuição de precisão por faixa (comparativo) ──
    if not eh_individual and resultados:
        for nome, df in resultados.items():
            if "distancia_km" not in df.columns:
                continue
            d = df["distancia_km"].dropna()
            if len(d) == 0:
                continue
            n = len(d)
            fx = pd.DataFrame([
                {"Faixa de erro": f"0 - {raio1:.0f} km", "Posições": int((d <= raio1).sum()),
                 "%": f"{(d <= raio1).mean()*100:.1f}"},
                {"Faixa de erro": f"{raio1:.0f} - {raio2:.0f} km",
                 "Posições": int(((d > raio1) & (d <= raio2)).sum()),
                 "%": f"{((d > raio1) & (d <= raio2)).mean()*100:.1f}"},
                {"Faixa de erro": f"{raio2:.0f} - {raio3:.0f} km",
                 "Posições": int(((d > raio2) & (d <= raio3)).sum()),
                 "%": f"{((d > raio2) & (d <= raio3)).mean()*100:.1f}"},
                {"Faixa de erro": f"acima de {raio3:.0f} km", "Posições": int((d > raio3).sum()),
                 "%": f"{(d > raio3).mean()*100:.1f}"},
            ])
            if pdf.get_y() > 235:
                pdf.add_page()
            _titulo(pdf, f"Precisão por Faixa - {_curto(nome)}")
            _tabela(pdf, fx)

    # ── Raio do sistema: faixas (ambos os modos) ──
    for d in dados:
        dtec = _dtec(d)
        if dtec is None or "raio_km" not in dtec.columns:
            continue
        rk = pd.to_numeric(dtec["raio_km"], errors="coerce").dropna()
        if len(rk) == 0:
            continue
        n = len(rk)
        fx = pd.DataFrame([
            {"Faixa de raio": f"0 - {raio1:.0f} km", "Posições": int((rk <= raio1).sum()),
             "%": f"{(rk <= raio1).mean()*100:.1f}"},
            {"Faixa de raio": f"{raio1:.0f} - {raio2:.0f} km",
             "Posições": int(((rk > raio1) & (rk <= raio2)).sum()),
             "%": f"{((rk > raio1) & (rk <= raio2)).mean()*100:.1f}"},
            {"Faixa de raio": f"{raio2:.0f} - {raio3:.0f} km",
             "Posições": int(((rk > raio2) & (rk <= raio3)).sum()),
             "%": f"{((rk > raio2) & (rk <= raio3)).mean()*100:.1f}"},
            {"Faixa de raio": f"acima de {raio3:.0f} km", "Posições": int((rk > raio3).sum()),
             "%": f"{(rk > raio3).mean()*100:.1f}"},
        ])
        if pdf.get_y() > 235:
            pdf.add_page()
        _titulo(pdf, f"Raio do Sistema por Faixa - {_curto(d.get('arquivo','-'))}")
        _tabela(pdf, fx)
        _nota(pdf, f"Raio médio informado: {rk.mean():.3f} km (min {rk.min():.2f}, "
                   f"max {rk.max():.2f}). O raio de incerteza é declarado pelo sistema "
                   f"para cada posição - raio menor = sistema mais confiante.")

    # ── Rede / tecnologia por equipamento ──
    linhas_rede = []
    for d in dados:
        dtec = _dtec(d)
        if dtec is None or "_tech" not in dtec.columns or dtec["_tech"].isna().all():
            continue
        total = len(dtec)
        c4 = int(dtec["_tech"].str.startswith("4G").sum())
        c2 = int(dtec["_tech"].str.startswith("2G").sum())
        ci_ = int((dtec["_tech"] == "Indefinido").sum())
        op = dtec["_operadora"].mode().iloc[0] if "_operadora" in dtec.columns and dtec["_operadora"].notna().any() else "-"
        bd = "-"
        if "_banda" in dtec.columns and (dtec["_banda"] != "-").any():
            bb = dtec[dtec["_banda"] != "-"]["_banda"].mode()
            bd = bb.iloc[0] if len(bb) else "-"
        linhas_rede.append({"Equipamento": _curto(d.get("arquivo", "-")),
            "Total": total, "4G": f"{c4/total*100:.0f}%", "2G": f"{c2/total*100:.0f}%",
            "Indefinido": f"{ci_/total*100:.0f}%", "Operadora": op, "Banda": bd})
    if linhas_rede:
        if pdf.get_y() > 235:
            pdf.add_page()
        _titulo(pdf, "Rede e Operadora")
        _tabela(pdf, pd.DataFrame(linhas_rede))
        _nota(pdf, "\"Indefinido\" = registro sem informação de rede no momento (comum em "
                   "registros recuperados do buffer, que sobem sem o dado da ERB).")

    # ── Qualidade GPS (satélites / DOP) ──
    linhas_gps = []
    for d in dados:
        dtec = _dtec(d)
        if dtec is None:
            continue
        reg = {"Equipamento": _curto(d.get("arquivo", "-"))}
        tem = False
        if "satellitenumber" in dtec.columns and dtec["satellitenumber"].notna().any():
            s = dtec["satellitenumber"].dropna()
            reg["Satélites (méd)"] = f"{s.mean():.1f}"
            reg["Satélites (min-max)"] = f"{int(s.min())}-{int(s.max())}"
            tem = True
        if "hdop" in dtec.columns and dtec["hdop"].notna().any():
            reg["HDOP médio"] = f"{dtec['hdop'].dropna().mean():.1f}"
            tem = True
        if tem:
            linhas_gps.append(reg)
    if linhas_gps:
        if pdf.get_y() > 235:
            pdf.add_page()
        _titulo(pdf, "Qualidade de GPS")
        _tabela(pdf, pd.DataFrame(linhas_gps))
        _nota(pdf, "Satélites e DOP só existem quando o GPS está ligado. Mais satélites "
                   "e DOP menor indicam melhor qualidade de posição.")

    # ── Latência e Buffer detalhado ──
    linhas_lat = []
    for d in dados:
        dtec = _dtec(d)
        if dtec is None or "_latencia_s" not in dtec.columns or dtec["_latencia_s"].isna().all():
            continue
        bufm = dtec["_buffer_bool"].fillna(False) if "_buffer_bool" in dtec.columns \
            else pd.Series(False, index=dtec.index)
        real = dtec[~bufm]["_latencia_s"].dropna()
        buf = dtec[bufm]["_latencia_s"].dropna()
        reg = {"Equipamento": _curto(d.get("arquivo", "-")),
               "Lat real média": f"{real.mean():.1f}s" if len(real) else "-",
               "Lat real máx": f"{real.max():.0f}s" if len(real) else "-",
               "% <=90s": f"{(real <= 90).mean()*100:.1f}" if len(real) else "-",
               "Reg. buffer": f"{len(buf)} ({len(buf)/len(dtec)*100:.0f}%)" if len(buf) else "0"}
        linhas_lat.append(reg)
    if linhas_lat:
        if pdf.get_y() > 235:
            pdf.add_page()
        _titulo(pdf, "Latência e Buffer")
        _tabela(pdf, pd.DataFrame(linhas_lat))
        _nota(pdf, "Latência = tempo entre o registro no módulo e a chegada ao servidor. "
                   "\"Lat real\" exclui os registros de buffer (que sobem atrasados após "
                   "perda de sinal e, por serem LIFO, não refletem a velocidade real).")

    # ── GPS válido × inválido ──
    linhas_gv = []
    for d in dados:
        dtec = _dtec(d)
        if dtec is None or "_gps_bool" not in dtec.columns or dtec["_gps_bool"].isna().all():
            continue
        gb = dtec["_gps_bool"].dropna()
        nv, ni, tot = int(gb.sum()), int((~gb).sum()), len(gb)
        linhas_gv.append({"Equipamento": _curto(d.get("arquivo", "-")),
            "GPS válido": f"{nv} ({nv/tot*100:.1f}%)",
            "GPS inválido": f"{ni} ({ni/tot*100:.1f}%)", "Total": tot})
    if linhas_gv:
        _quebra(pdf)
        _titulo(pdf, "GPS Valido x Invalido")
        _tabela(pdf, pd.DataFrame(linhas_gv))
        _nota(pdf, "Um fix de GPS e valido quando o modulo obteve posicao real por "
                   "satelite; invalido quando nao conseguiu - nesses casos a posicao "
                   "costuma vir estimada por ERB.")

    # ── Bateria ──
    linhas_bat = []
    for d in dados:
        dtec = _dtec(d)
        if dtec is None:
            continue
        bcol = "_bateria_pct" if "_bateria_pct" in dtec.columns else "_bateria_pct_csv"
        if bcol not in dtec.columns or dtec[bcol].isna().all():
            continue
        bp = dtec[bcol].dropna()
        if len(bp) < 2:
            continue
        linhas_bat.append({"Equipamento": _curto(d.get("arquivo", "-")),
            "Início": f"{bp.iloc[0]:.0f}%", "Fim": f"{bp.iloc[-1]:.0f}%",
            "Consumo": f"{bp.iloc[0]-bp.iloc[-1]:.0f}%",
            "Mínima": f"{bp.min():.0f}%"})
    if linhas_bat:
        _quebra(pdf)
        _titulo(pdf, "Bateria")
        _tabela(pdf, pd.DataFrame(linhas_bat))

    # ── Movimento ──
    linhas_mov = []
    for d in dados:
        dtec = _dtec(d)
        if dtec is None or "speed" not in dtec.columns or dtec["speed"].isna().all():
            continue
        s = dtec["speed"].dropna()
        linhas_mov.append({"Equipamento": _curto(d.get("arquivo", "-")),
            "Vel. média": f"{s.mean():.1f} km/h", "Vel. máxima": f"{s.max():.1f} km/h",
            "% em movimento": f"{(s > 3).mean()*100:.1f}%", "Registros": len(s)})
    if linhas_mov:
        _quebra(pdf)
        _titulo(pdf, "Movimento")
        _tabela(pdf, pd.DataFrame(linhas_mov))

    # ── Buffer LIFO (comparativo e individual) ──
    from services.analise import analisar_buffer_lifo
    linhas_lifo = []
    for d in dados:
        dtec = _dtec(d)
        if dtec is None:
            continue
        try:
            r = analisar_buffer_lifo(dtec)
        except Exception:
            r = None
        if not r or r.get("n_episodios", 0) == 0:
            continue
        linhas_lifo.append({"Equipamento": _curto(d.get("arquivo", "-")),
            "Episódios": r["n_episodios"],
            "% em ordem LIFO": f"{r.get('pct_conforme', 0):.1f}%",
            "Reg. fora de ordem": r.get("registros_fora_ordem", 0)})
    if linhas_lifo:
        _quebra(pdf)
        _titulo(pdf, "Buffer - Verificacao de Ordem LIFO")
        _tabela(pdf, pd.DataFrame(linhas_lifo))
        _nota(pdf, "Ao perder sinal, o modulo guarda os pontos e, ao reconectar, sobe "
                   "primeiro os mais recentes (LIFO). Esta verificacao confirma se a "
                   "ordem de chegada respeita esse padrao.")

    out = pdf.output()
    return bytes(out)
