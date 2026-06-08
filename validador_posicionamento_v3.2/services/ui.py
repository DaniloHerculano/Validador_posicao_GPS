"""
ui.py — Componentes visuais reutilizáveis e tema CLARO Stoneridge.
"""
import base64
from pathlib import Path
import streamlit as st

from services.config import PLOTLY_THEME


def tile(label, value, sub="", cc="") -> str:
    return (
        f'<div class="m-tile {cc}">'
        f'<div class="m-tile-label">{label}</div>'
        f'<div class="m-tile-val">{value}</div>'
        f'<div class="m-tile-sub">{sub}</div></div>'
    )


def grid(*tiles_html):
    st.markdown(f'<div class="metric-grid">{"".join(tiles_html)}</div>',
                unsafe_allow_html=True)


def sec(txt: str):
    st.markdown(f'<div class="sec-hdr">// {txt}</div>', unsafe_allow_html=True)


def aplica_tema(fig, h=300):
    fig.update_layout(**PLOTLY_THEME, height=h)
    return fig


def badge(tipo: str) -> str:
    if tipo == "GPS Real":
        return '<span class="badge badge-gps">GPS Real</span>'
    if tipo == "Posição Estimada":
        return '<span class="badge badge-est">Pos. Estimada</span>'
    return '<span class="badge badge-unk">Desconhecido</span>'


def logo_sidebar():
    """Renderiza o logo Stoneridge no topo da sidebar."""
    caminho = Path(__file__).parent.parent / "assets" / "stoneridge_logo.png"
    if caminho.exists():
        b64 = base64.b64encode(caminho.read_bytes()).decode()
        st.markdown(
            f'<div class="sidebar-logo"><img src="data:image/png;base64,{b64}"/></div>',
            unsafe_allow_html=True)


def carregar_css():
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&family=Barlow:wght@400;500;600;700&display=swap');
:root{
  --red:#dd0933;        /* Pantone 186 */
  --red-dark:#b80d2f;   /* Pantone 187 */
  --slate:#2c3946;      /* Pantone 432 */
  --light:#d5e2f2;      /* Pantone 650 */
  --bg:#f5f7fa;         /* fundo claro */
  --surface:#ffffff;    /* cartões */
  --surface2:#eef2f7;   /* hover/realce */
  --border:#dce4ee;
  --text:#1f2a36;       /* texto principal */
  --muted:#6b7f8f;      /* texto secundário */
}
html,body,[class*="css"]{font-family:'Barlow',sans-serif;color:var(--text);}
.stApp{background:var(--bg);}

/* Sidebar clara */
section[data-testid="stSidebar"]{background:#ffffff!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] *{color:var(--text)!important;}
section[data-testid="stSidebar"] h3{color:var(--slate)!important;}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stNumberInput label{
  color:var(--slate)!important;font-size:.76rem!important;font-weight:600!important;
  text-transform:uppercase;letter-spacing:.06em;}
.sidebar-logo{padding:.4rem .2rem 1rem .2rem;border-bottom:1px solid var(--border);margin-bottom:1rem;}
.sidebar-logo img{width:100%;max-width:210px;display:block;}

.block-container{padding-top:2.2rem!important;padding-bottom:2rem;}
h1,h2,h3,h4{font-family:'Barlow Condensed',sans-serif!important;font-weight:700!important;color:var(--slate)!important;}

.sec-hdr{font-family:'Barlow Condensed',sans-serif;font-size:.72rem;font-weight:700;color:var(--red);
  text-transform:uppercase;letter-spacing:.16em;border-bottom:2px solid var(--border);
  padding-bottom:.45rem;margin:1.8rem 0 1.1rem 0;}

/* HERO — corrigido: line-height e padding para não cortar */
.hero-wrap{display:flex;align-items:center;gap:1rem;margin:.2rem 0 .6rem 0;}
.hero-bar{width:6px;align-self:stretch;min-height:54px;background:var(--red);border-radius:3px;flex-shrink:0;}
.hero-title{font-family:'Barlow Condensed',sans-serif;font-size:2.3rem;font-weight:800;
  color:var(--slate);line-height:1.15;padding:.05em 0;letter-spacing:.005em;}
.hero-sub{font-size:.82rem;color:var(--muted);letter-spacing:.02em;margin-top:.15rem;}

/* Tabela de arquivos */
.file-table{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--border);
  border-radius:10px;overflow:hidden;margin-bottom:1.2rem;font-size:.84rem;
  box-shadow:0 1px 3px rgba(44,57,70,.06);}
.file-table thead tr{background:var(--slate);}
.file-table th{padding:10px 14px;text-align:left;font-family:'Barlow Condensed',sans-serif;
  font-size:.7rem;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:.1em;}
.file-table td{padding:9px 14px;border-top:1px solid var(--border);color:var(--text);}
.file-table tr:hover td{background:var(--surface2);}

/* Badges */
.badge{padding:2px 11px;border-radius:999px;font-size:.7rem;font-family:'Barlow Condensed',sans-serif;
  font-weight:700;letter-spacing:.05em;text-transform:uppercase;}
.badge-gps{background:#e4f5ec;color:#1f8b4c;border:1px solid #b5e3c8;}
.badge-est{background:#fdeede;color:#c2691a;border:1px solid #f5cfa0;}
.badge-unk{background:#eceef5;color:#5b6bb0;border:1px solid #c9cfe8;}

/* Métricas */
.metric-grid{display:flex;gap:.7rem;flex-wrap:wrap;margin-bottom:1rem;}
.m-tile{background:var(--surface);border:1px solid var(--border);border-top:3px solid var(--red);
  border-radius:9px;padding:.85rem 1.15rem;min-width:115px;flex:1;box-shadow:0 1px 3px rgba(44,57,70,.05);}
.m-tile.green{border-top-color:#1f8b4c;}.m-tile.amber{border-top-color:#e08a1e;}
.m-tile.blue{border-top-color:#2477b3;}
.m-tile-label{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;
  font-family:'Barlow Condensed',sans-serif;font-weight:700;margin-bottom:.2rem;}
.m-tile-val{font-family:'Barlow Condensed',sans-serif;font-size:1.7rem;font-weight:800;color:var(--slate);line-height:1.05;}
.m-tile-sub{font-size:.7rem;color:var(--muted);margin-top:.15rem;}

/* Botões */
.stButton>button{background:var(--red)!important;color:#fff!important;border:none!important;border-radius:7px!important;
  font-family:'Barlow Condensed',sans-serif!important;font-weight:700!important;font-size:1rem!important;
  letter-spacing:.05em!important;padding:.55rem 2rem!important;width:100%!important;transition:background .2s!important;
  box-shadow:0 2px 6px rgba(221,9,51,.25)!important;}
.stButton>button:hover{background:var(--red-dark)!important;}
.stDownloadButton>button{background:var(--slate)!important;color:#fff!important;border:none!important;
  border-radius:7px!important;font-family:'Barlow Condensed',sans-serif!important;font-weight:700!important;}
.stDownloadButton>button:hover{background:#1f2a36!important;}

/* Inputs */
.stSelectbox>div>div,.stMultiSelect>div>div{background:var(--surface)!important;border:1px solid var(--border)!important;
  border-radius:7px!important;color:var(--text)!important;}
.stNumberInput>div>div>input{background:var(--surface)!important;border:1px solid var(--border)!important;
  color:var(--text)!important;border-radius:7px!important;}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{background:var(--surface);gap:4px;padding:5px;border-radius:9px;
  border:1px solid var(--border);flex-wrap:wrap;box-shadow:0 1px 3px rgba(44,57,70,.05);}
.stTabs [data-baseweb="tab"]{background:transparent;color:var(--muted);border-radius:6px;
  font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:.9rem;letter-spacing:.02em;padding:.3rem .8rem;}
.stTabs [aria-selected="true"]{background:var(--red)!important;color:#fff!important;}

/* Expanders (painéis por rastreador) */
.streamlit-expanderHeader,details>summary{font-family:'Barlow Condensed',sans-serif!important;font-weight:700!important;}
div[data-testid="stExpander"]{border:1px solid var(--border)!important;border-radius:10px!important;
  background:var(--surface)!important;margin-bottom:.7rem!important;box-shadow:0 1px 3px rgba(44,57,70,.05);overflow:hidden;}
div[data-testid="stExpander"] summary{padding:.85rem 1.1rem!important;font-size:1rem!important;color:var(--slate)!important;}
div[data-testid="stExpander"] summary:hover{background:var(--surface2)!important;color:var(--red)!important;}

/* Dataframe */
div[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:9px!important;overflow:hidden;}

/* Alerts mais suaves */
div[data-testid="stAlert"]{border-radius:9px;}

hr{border-color:var(--border)!important;}
.js-plotly-plot{border-radius:9px;overflow:hidden;}
</style>
"""
