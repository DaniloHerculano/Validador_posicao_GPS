"""
config.py — Constantes, paleta de cores Stoneridge e tema dos gráficos.
"""

# ── Mapeamento de operadoras por código MCC+MNC (campo networkinfo) ──
OPERADORAS = {
    "72402": "TIM", "72403": "TIM", "72404": "TIM", "72454": "TIM", "72406": "TIM",
    "72405": "Claro", "72438": "Claro",
    "72410": "Vivo", "72411": "Vivo", "72423": "Vivo", "72431": "Vivo", "72432": "Vivo",
}

# ── Mapeamento de tecnologia de rede (string do networkinfo → geração) ──
TECH_MAP = {
    "FDD LTE": "4G", "TDD LTE": "4G", "LTE": "4G",
    "EMTC": "4G (LTE-M)", "NB-IOT": "4G (NB-IoT)",
    "WCDMA": "3G", "UMTS": "3G", "HSPA": "3G",
    "GSM": "2G", "GPRS": "2G", "EDGE": "2G",
    "NO SERVICE": "Sem Sinal",
}

# ── Paleta Stoneridge Brasil (Pantone) ──
SR_RED   = "#dd0933"   # Pantone 186 — principal
SR_RED2  = "#b80d2f"   # Pantone 187
SR_SLATE = "#2c3946"   # Pantone 432
SR_LIGHT = "#d5e2f2"   # Pantone 650
SR_BLACK = "#0d0d0d"   # 100% Black
SR_WHITE = "#ffffff"

# ── Tema base dos gráficos Plotly (CLARO) ──
PLOTLY_THEME = dict(
    template="plotly_white",
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f5f7fa",
    font=dict(family="Barlow, sans-serif", color="#1f2a36", size=11),
)

# ── Paletas auxiliares (otimizadas p/ fundo claro) ──
COLORS_TECH  = [SR_RED, "#e08a1e", "#2477b3", "#7c5cd0", "#1f8b4c", "#6b7f8f"]
COLORS_RAIOS = ["#1f8b4c", "#e08a1e", "#dd7016", "#d92020"]
PALETA       = [SR_RED, "#2477b3", "#e08a1e", "#7c5cd0", SR_SLATE, "#1f8b4c", "#c2691a"]

# ── Faixas de latência (segundos) ──
LATENCIA_BINS   = [-float("inf"), 20, 90, 180, 240, 300, float("inf")]
LATENCIA_LABELS = ["<20s", "20–90s", "90–180s", "180–240s", "240–300s", ">300s"]
LATENCIA_CORES  = ["#1f8b4c", "#5cb87f", "#e08a1e", "#dd7016", "#d92020", SR_RED2]
