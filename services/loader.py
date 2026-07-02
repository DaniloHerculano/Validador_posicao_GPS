"""
loader.py — Leitura de CSV (log técnico) e XLS (posição estimada/convertida),
agrupamento por equipamento e fusão das duas fontes por horário.
"""
import re
import os
import pandas as pd
from geopy.distance import geodesic

from services.config import OPERADORAS, TECH_MAP


# ── Identificação ─────────────────────────────────────────────────────────────
def nome_base(nome_arquivo: str) -> str:
    """Remove a extensão para agrupar CSV + XLS do mesmo equipamento."""
    return os.path.splitext(nome_arquivo)[0]


def extrair_pin(nome_arquivo: str) -> str:
    m = re.search(r"(\d{6,})", nome_arquivo)
    return m.group(1) if m else "N/A"


def extrair_modelo(nome_arquivo: str) -> str:
    m = re.search(r"(RI\d{3,})", nome_arquivo, re.IGNORECASE)
    return m.group(1).upper() if m else "—"


# ── Parsing de campos ─────────────────────────────────────────────────────────
def _normaliza_banda(texto: str, tech: str) -> str:
    """Normaliza o campo de banda: 'GSM 1800' → 'GSM1800', 'LTE BAND 28' → 'LTE B28'."""
    if not texto:
        return "—"
    t = texto.upper().strip()
    m = re.search(r"LTE\s*BAND\s*(\d+)", t)
    if m:
        return f"LTE B{m.group(1)}"
    m = re.search(r"GSM\s*(\d+)", t)
    if m:
        return f"GSM{m.group(1)}"
    m = re.search(r"(WCDMA|UMTS|HSPA|HSDPA)\D*(\d+)?", t)
    if m:
        return f"{m.group(1)}{(' B'+m.group(2)) if m.group(2) else ''}"
    return texto.strip() or "—"


def parse_networkinfo(info) -> tuple:
    """networkinfo: "FDD LTE","72405","LTE BAND 7",2950 → (tecnologia, operadora, banda)."""
    if pd.isna(info) or str(info).strip() in ("", "NO SERVICE"):
        return "Sem Sinal", "Desconhecido", "—"
    s = str(info).strip()
    if "NO SERVICE" in s.upper():
        return "Sem Sinal", "Desconhecido", "—"
    parts = [p.strip().strip('"').strip("'") for p in s.split(",")]
    tech = "Desconhecido"
    if parts:
        raw = parts[0].upper()
        for kw, label in TECH_MAP.items():
            if kw.upper() in raw:
                tech = label
                break
    operadora = "Desconhecido"
    if len(parts) > 1:
        operadora = OPERADORAS.get(parts[1].strip(), "Desconhecido")
    banda = _normaliza_banda(parts[2] if len(parts) > 2 else "", tech)
    return tech, operadora, banda


def bat_csv_para_pct(valor) -> float:
    """CSV: 0–20 → %. Valores fora da faixa (ex.: 253) viram None."""
    try:
        v = float(valor)
        if v < 0 or v > 20:
            return None
        return round((v / 20.0) * 100, 1)
    except Exception:
        return None


def bat_xls_para_pct(valor) -> float:
    """'45 %' / '45' / 45 → 45.0"""
    if pd.isna(valor):
        return None
    try:
        return float(str(valor).replace("%", "").strip())
    except Exception:
        return None


def calcular_distancia(lat1, lon1, lat2, lon2) -> float:
    try:
        return geodesic((float(lat1), float(lon1)), (float(lat2), float(lon2))).km
    except Exception:
        return None


# ── Leitura crua ──────────────────────────────────────────────────────────────
def ler_kml(arquivo) -> pd.DataFrame:
    """
    Extrai do KML (portal SSO/PST) os pontos que possuem 'Raio:' — o raio de
    incerteza que o próprio sistema calcula para cada posição estimada.
    Retorna DataFrame com datetime_module e raio_km (metros convertidos para km).
    Placemarks de polígono (o círculo desenhado) não têm 'Raio:' e são ignorados.
    """
    # Ler bytes e decodificar tolerando latin1/utf-8
    if hasattr(arquivo, "read"):
        if hasattr(arquivo, "seek"):
            arquivo.seek(0)
        raw = arquivo.read()
        if isinstance(raw, bytes):
            try:
                texto = raw.decode("utf-8")
            except UnicodeDecodeError:
                texto = raw.decode("latin1", errors="replace")
        else:
            texto = raw
    else:
        try:
            texto = open(arquivo, encoding="utf-8").read()
        except UnicodeDecodeError:
            texto = open(arquivo, encoding="latin1", errors="replace").read()

    registros = []
    for pm in re.findall(r"<Placemark>.*?</Placemark>", texto, re.DOTALL):
        if "Raio:" not in pm:
            continue
        m_nome = re.search(r"<name>(.*?)</name>", pm, re.DOTALL)
        m_raio = re.search(r"Raio:\s*([\d.]+)", pm)
        if not (m_nome and m_raio):
            continue
        dt = pd.to_datetime(m_nome.group(1).strip(), dayfirst=True, errors="coerce")
        if pd.isna(dt):
            continue
        raio_m = float(m_raio.group(1))
        registros.append({"datetime_module": dt, "raio_km": round(raio_m / 1000.0, 4)})

    df = pd.DataFrame(registros)
    if len(df):
        df = df.sort_values("datetime_module").reset_index(drop=True)
    return df


def ler_csv(arquivo) -> pd.DataFrame:
    df = pd.read_csv(arquivo, sep=";", low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ["datetime_module", "datetime_server", "datetime_gps", "datetime_trilateration"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["latitude", "longitude", "altitude", "heading", "speed",
                "hdop", "vdop", "sdop", "satellitenumber", "voltage",
                "xaccel", "yaccel", "zaccel"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "internalbatterylevel" in df.columns:
        df["internalbatterylevel"] = pd.to_numeric(df["internalbatterylevel"], errors="coerce")
    return df


def ler_xls(arquivo) -> pd.DataFrame:
    """Tolera .xls (xlrd), .xlsx (openpyxl) ou HTML disfarçado."""
    erros = []
    for kwargs in [{}, {"engine": "xlrd"}, {"engine": "openpyxl"}]:
        try:
            if hasattr(arquivo, "seek"):
                arquivo.seek(0)
            return pd.read_excel(arquivo, **kwargs)
        except Exception as e:
            erros.append(str(e))
    try:
        if hasattr(arquivo, "seek"):
            arquivo.seek(0)
        return pd.read_html(arquivo)[0]
    except Exception as e:
        erros.append(str(e))
    raise Exception("Não foi possível ler o XLS: " + " | ".join(erros[:2]))


# ── Normalização do XLS ───────────────────────────────────────────────────────
def normalizar_xls(df_xls: pd.DataFrame) -> pd.DataFrame:
    df = df_xls.copy()
    ren = {
        "Data do Módulo": "datetime_module", "Data do Servidor": "datetime_server",
        "Data do GPS": "datetime_gps", "Data do ERB": "datetime_erb",
        "Latitude": "latitude", "Longitude": "longitude", "Velocidade": "speed",
        "Endereço": "endereco", "Posição Estimada": "pos_estimada",
        "GPS Válido?": "gps_valido", "Sinal": "sinal", "Tipo": "tipo_evento",
        "Nível da Bateria": "nivel_bateria_xls", "Status da bateria": "status_bateria",
        "Temperatura": "temperatura", "Umidade": "umidade", "Ignição": "ignicao_xls",
    }
    df = df.rename(columns={k: v for k, v in ren.items() if k in df.columns})
    for col in ["datetime_module", "datetime_server", "datetime_gps", "datetime_erb"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
    for col in ["latitude", "longitude", "speed"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "gps_valido" in df.columns:
        s = df["gps_valido"].astype(str).str.strip().str.lower()
        df["_gps_bool"] = s.isin(["válido", "valido"])
    if "pos_estimada" in df.columns:
        df["_estimada_bool"] = df["pos_estimada"].astype(str).str.strip().str.lower().eq("sim")
    if "nivel_bateria_xls" in df.columns:
        df["_bateria_pct"] = df["nivel_bateria_xls"].apply(bat_xls_para_pct)
    return df


# ── Enriquecimento do CSV ─────────────────────────────────────────────────────
def enriquecer_csv(df: pd.DataFrame) -> pd.DataFrame:
    if "networkinfo" in df.columns:
        p = df["networkinfo"].apply(parse_networkinfo)
        df["_tech"] = p.apply(lambda x: x[0])
        df["_operadora"] = p.apply(lambda x: x[1])
        df["_banda"] = p.apply(lambda x: x[2])
    if "internalbatterylevel" in df.columns:
        df["_bateria_pct_csv"] = df["internalbatterylevel"].apply(bat_csv_para_pct)
    if "datetime_module" in df.columns and "datetime_server" in df.columns:
        df["_latencia_s"] = (df["datetime_server"] - df["datetime_module"]).dt.total_seconds()
    if "gps" in df.columns:
        df["_gps_bool_csv"] = df["gps"].astype(str).str.lower().isin(["t", "true", "1"])
    if "movementsensor" in df.columns:
        df["_movimento"] = df["movementsensor"].astype(str).str.lower().isin(["t", "true", "1"])
    return df


# ── Fusão XLS + CSV ───────────────────────────────────────────────────────────
COLS_TEC_CSV = ["_tech", "_operadora", "_banda", "_latencia_s", "satellitenumber",
                "hdop", "vdop", "sdop", "altitude", "heading", "transmissiontype",
                "networktype", "bufferstatus", "_movimento", "_bateria_pct_csv", "voltage"]


def fundir(df_xls: pd.DataFrame, df_csv: pd.DataFrame, tol_seg=60) -> pd.DataFrame:
    base = df_xls.dropna(subset=["datetime_module"]).sort_values("datetime_module").copy()
    if df_csv is None or len(df_csv) == 0 or "datetime_module" not in df_csv.columns:
        return base
    tec = df_csv.dropna(subset=["datetime_module"]).sort_values("datetime_module").copy()
    cols = [c for c in COLS_TEC_CSV if c in tec.columns]
    tec = tec[["datetime_module"] + cols]
    return pd.merge_asof(base, tec, on="datetime_module", direction="nearest",
                         tolerance=pd.Timedelta(seconds=tol_seg))


def _anexar_raio_kml(df, df_kml, tol_seg=60):
    """Casa o raio_km do KML a cada ponto por horário (vizinho mais próximo)."""
    if df_kml is None or len(df_kml) == 0 or "datetime_module" not in df.columns:
        return df
    base = df.dropna(subset=["datetime_module"]).sort_values("datetime_module").copy()
    kml = df_kml.dropna(subset=["datetime_module"]).sort_values("datetime_module").copy()
    fundido = pd.merge_asof(base, kml[["datetime_module", "raio_km"]],
                            on="datetime_module", direction="nearest",
                            tolerance=pd.Timedelta(seconds=tol_seg))
    return fundido


def consolidar_equipamento(nome, csv_file, xls_file, kml_file=None, tol_fusao=60) -> dict:
    """Carrega e funde os arquivos de um equipamento. Posição: XLS > CSV. Raio: KML."""
    df_csv = enriquecer_csv(ler_csv(csv_file)) if csv_file is not None else None
    df_xls = normalizar_xls(ler_xls(xls_file)) if xls_file is not None else None
    df_kml = ler_kml(kml_file) if kml_file is not None else None

    if df_xls is not None:
        df = fundir(df_xls, df_csv, tol_seg=tol_fusao)
        fonte = "XLS+CSV" if df_csv is not None else "XLS"
        if "_bateria_pct" not in df.columns or df["_bateria_pct"].isna().all():
            if "_bateria_pct_csv" in df.columns:
                df["_bateria_pct"] = df["_bateria_pct_csv"]
        if "_estimada_bool" in df.columns and df["_estimada_bool"].notna().any():
            frac_est = df["_estimada_bool"].mean()
            if 0.05 < frac_est < 0.95:
                tipo = "Misto (Real + Estimada)"
            elif frac_est >= 0.95:
                tipo = "Posição Estimada"
            else:
                tipo = "GPS Real"
        else:
            tipo = "Desconhecido"
    elif df_csv is not None:
        df = df_csv.copy()
        if "_bateria_pct_csv" in df.columns:
            df["_bateria_pct"] = df["_bateria_pct_csv"]
        if "_gps_bool_csv" in df.columns:
            df["_gps_bool"] = df["_gps_bool_csv"]
        fonte = "CSV"
        gp = df["_gps_bool_csv"] if "_gps_bool_csv" in df.columns else pd.Series([False])
        tipo = "GPS Real" if gp.mean() > 0.5 else "Posição Estimada"
    else:
        raise Exception(f"{nome}: nenhum arquivo válido.")

    # Anexar raio do sistema (KML), se houver
    tem_raio = False
    if df_kml is not None and len(df_kml) > 0:
        df = _anexar_raio_kml(df, df_kml, tol_seg=max(tol_fusao, 120))
        tem_raio = "raio_km" in df.columns and df["raio_km"].notna().any()
        if tem_raio:
            fonte = fonte + "+KML"

    return {"arquivo": nome, "pin": extrair_pin(nome), "modelo": extrair_modelo(nome),
            "tipo": tipo, "fonte": fonte, "registros": len(df),
            "tem_raio": tem_raio, "df": df,
            "df_tecnico": df_csv if df_csv is not None else df}
