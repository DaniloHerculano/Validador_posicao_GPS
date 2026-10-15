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
    erros = pd.concat([df["distancia_km"].dropna() for df in resultados.values()
                       if len(df)], ignore_index=True) if resultados else pd.Series(dtype=float)
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

    # ── Precisão (comparativo) ──
    if not eh_individual and resultados:
        linhas = []
        for nome, df in resultados.items():
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
                     for n, df in resultados.items() if len(df["distancia_km"].dropna())]
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

    out = pdf.output()
    return bytes(out)
