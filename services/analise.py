"""
analise.py — Sincronização por horário entre referência e comparados,
e cálculo de métricas de precisão.
"""
import pandas as pd
import numpy as np
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
        raio = row.get("raio_km", None)
        dentro_raio = None
        if raio is not None and pd.notna(raio) and dist is not None:
            dentro_raio = bool(dist <= raio)
        resultados.append({
            "horario_ref": r["datetime_module"], "horario_comp": t,
            "dif_seg": abs((r["datetime_module"] - t).total_seconds()),
            "lat_ref": r["latitude"], "lon_ref": r["longitude"],
            "lat_comp": row["latitude"], "lon_comp": row["longitude"],
            "distancia_km": dist,
            "raio_km": raio if (raio is not None and pd.notna(raio)) else None,
            "dentro_raio": dentro_raio,
            "endereco_comp": row.get("endereco", None),
            "estimada_comp": row.get("_estimada_bool", None),
            "gps_valido_comp": row.get("_gps_bool", None),
            "_tech_comp": row.get("_tech", "N/A"),
            "_operadora_comp": row.get("_operadora", "N/A"),
            "_banda_comp": row.get("_banda", "—"),
        })
    return pd.DataFrame(resultados)


def resumo_raio(df: pd.DataFrame) -> dict:
    """Métricas de validação contra o raio do sistema (KML)."""
    if len(df) == 0 or "dentro_raio" not in df.columns:
        return None
    val = df.dropna(subset=["dentro_raio", "distancia_km", "raio_km"])
    if len(val) == 0:
        return None
    return {
        "pontos": len(val),
        "dentro": int(val["dentro_raio"].sum()),
        "pct_dentro": round(val["dentro_raio"].mean() * 100, 1),
        "raio_medio": round(val["raio_km"].mean(), 3),
        "raio_min": round(val["raio_km"].min(), 3),
        "raio_max": round(val["raio_km"].max(), 3),
    }


def analisar_buffer_lifo(df_raw: pd.DataFrame) -> dict:
    """
    Verifica se a recuperação do buffer segue a ordem LIFO esperada.

    Quando o módulo perde sinal, ele armazena os registros localmente; ao
    reconectar, o esperado é que suba primeiro os pontos mais recentes
    (datetime_module maior) e só depois os mais antigos — ou seja, à medida
    que o datetime_server avança dentro da rajada de recuperação, o
    datetime_module deveria ser não-crescente.

    Agrupa os registros marcados como buffer em "episódios" (rajadas
    contínuas, na ordem de chegada ao servidor) e, para cada episódio,
    calcula:
      - taxa de pares fora de ordem (violações de "não-crescente")
      - correlação de ordem (rank) entre a posição de chegada e o
        datetime_module — próxima de -1 indica LIFO perfeito

    Retorna None se não houver dados suficientes (sem colunas de
    data/hora ou sem indicação de buffer).
    """
    if "datetime_module" not in df_raw.columns or "datetime_server" not in df_raw.columns:
        return None
    if "_buffer_bool" in df_raw.columns:
        buf_mask_full = df_raw["_buffer_bool"].fillna(False)
    elif "bufferstatus" in df_raw.columns:
        buf_mask_full = df_raw["bufferstatus"].astype(str).str.strip().str.lower().isin(
            ["t", "true", "1"])
    else:
        return None

    df = df_raw.dropna(subset=["datetime_module", "datetime_server"]).copy()
    if len(df) == 0:
        return None
    df["_buf"] = buf_mask_full.reindex(df.index).fillna(False)
    df = df.sort_values("datetime_server").reset_index(drop=True)
    df["_ep"] = (df["_buf"] != df["_buf"].shift()).cumsum()

    episodios = []
    for ep_id, g in df[df["_buf"]].groupby("_ep"):
        if len(g) < 2:
            continue
        dm = g["datetime_module"].values
        n = len(dm)
        viol = 0
        for i in range(n):
            for j in range(i + 1, n):
                if dm[j] > dm[i]:
                    viol += 1
        total_pares = n * (n - 1) // 2
        conforme = (viol == 0)
        rx = pd.Series(range(n)).rank().values
        ry = pd.Series(dm).rank().values
        rho = (np.corrcoef(rx, ry)[0, 1]
               if (np.std(rx) > 0 and np.std(ry) > 0) else np.nan)
        episodios.append({
            "episodio": int(ep_id), "n_registros": n,
            "inicio_server": g["datetime_server"].iloc[0],
            "fim_server": g["datetime_server"].iloc[-1],
            "modulo_mais_novo": g["datetime_module"].max(),
            "modulo_mais_antigo": g["datetime_module"].min(),
            "violacoes": viol, "pares_totais": total_pares,
            "taxa_desordem_pct": round(viol / total_pares * 100, 1) if total_pares else 0.0,
            "rho_ordem": round(rho, 3) if pd.notna(rho) else None,
            "conforme_lifo": conforme,
        })

    if not episodios:
        return None

    ep_df = pd.DataFrame(episodios)
    n_conforme = int(ep_df["conforme_lifo"].sum())
    n_total = len(ep_df)
    return {
        "episodios_df": ep_df,
        "n_episodios": n_total,
        "n_conforme": n_conforme,
        "pct_conforme": round(n_conforme / n_total * 100, 1),
        "registros_em_episodios": int(ep_df["n_registros"].sum()),
        "registros_fora_ordem": int(ep_df.loc[~ep_df["conforme_lifo"], "n_registros"].sum()),
        "rho_medio": (round(ep_df["rho_ordem"].dropna().mean(), 3)
                      if ep_df["rho_ordem"].notna().any() else None),
    }


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
