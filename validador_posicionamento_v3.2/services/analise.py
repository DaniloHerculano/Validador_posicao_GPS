"""
analise.py — Sincronização por horário entre referência e comparados,
e cálculo de métricas de precisão.
"""
import pandas as pd
from services.loader import calcular_distancia


def sincronizar(df_ref: pd.DataFrame, df_comp: pd.DataFrame, tol_min: int) -> pd.DataFrame:
    """
    Para cada registro do comparado, encontra o ponto mais próximo no tempo
    na referência (dentro da tolerância) e calcula a distância geodésica.
    Usa lat/lon já consolidadas (XLS > CSV). Inclui endereço/estimada quando houver.
    """
    resultados = []
    tol = pd.Timedelta(minutes=tol_min)
    ref = df_ref.dropna(subset=["datetime_module", "latitude", "longitude"])
    ref_times = ref["datetime_module"]
    if ref_times.empty:
        return pd.DataFrame()

    for _, row in df_comp.iterrows():
        t = row.get("datetime_module")
        if pd.isna(t) or pd.isna(row.get("latitude")) or pd.isna(row.get("longitude")):
            continue
        diffs = (ref_times - t).abs()
        if diffs.empty:
            continue
        idx = diffs.idxmin()
        if diffs.loc[idx] > tol:
            continue
        r = ref.loc[idx]
        dist = calcular_distancia(r["latitude"], r["longitude"],
                                  row["latitude"], row["longitude"])
        resultados.append({
            "horario_ref": r["datetime_module"], "horario_comp": t,
            "dif_seg": abs((r["datetime_module"] - t).total_seconds()),
            "lat_ref": r["latitude"], "lon_ref": r["longitude"],
            "lat_comp": row["latitude"], "lon_comp": row["longitude"],
            "distancia_km": dist,
            "endereco_comp": row.get("endereco", None),
            "estimada_comp": row.get("_estimada_bool", None),
            "gps_valido_comp": row.get("_gps_bool", None),
            "_tech_comp": row.get("_tech", "N/A"),
            "_operadora_comp": row.get("_operadora", "N/A"),
        })
    return pd.DataFrame(resultados)


def gerar_resumo(df: pd.DataFrame, raio1: float, raio2: float, raio3: float) -> dict:
    if len(df) == 0 or "distancia_km" not in df.columns:
        return None
    d = df["distancia_km"].dropna()
    if len(d) == 0:
        return None
    return {
        "sincronizacoes": len(d),
        "erro_medio": round(d.mean(), 3), "erro_max": round(d.max(), 3),
        "erro_min": round(d.min(), 3), "mediana": round(d.median(), 3),
        "pct_r1": round((d <= raio1).mean() * 100, 1),
        "pct_r2": round((d <= raio2).mean() * 100, 1),
        "pct_r3": round((d <= raio3).mean() * 100, 1),
    }
