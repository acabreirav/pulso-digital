"""Métricas del Radar de Tracción — funciones puras (CLAUDE.md §8).

Todas reciben datos simples (números, listas, dicts del esquema interno) y
devuelven resultados sin tocar disco ni red, para que sean testeables.
Regla de la casa: mediana, no promedio, en métricas por-video (un viral
distorsiona el promedio).

Convención: cuando no hay datos suficientes se devuelve None (o estado
"sin datos"), nunca se inventa un cero — el dashboard distingue "no se
puede calcular todavía" de "es cero de verdad".
"""

from datetime import datetime, timezone


# ---------- utilidades ----------

def mediana(valores: list) -> float | None:
    """Mediana clásica. None si la lista viene vacía."""
    limpios = sorted(v for v in valores if v is not None)
    if not limpios:
        return None
    n = len(limpios)
    mitad = n // 2
    if n % 2:
        return float(limpios[mitad])
    return (limpios[mitad - 1] + limpios[mitad]) / 2


def _fecha(iso: str) -> datetime:
    """Parsea fechas ISO (con o sin Z) a datetime consciente de zona."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ---------- por cuenta ----------

def crecimiento_seguidores(f_inicio: int | None, f_fin: int | None) -> dict | None:
    """Crecimiento absoluto y porcentual entre dos fotos. None si falta una."""
    if f_inicio is None or f_fin is None:
        return None
    absoluto = f_fin - f_inicio
    porcentual = (absoluto / f_inicio * 100) if f_inicio else None
    return {"absoluto": absoluto, "porcentual": porcentual}


def aceleracion(serie: list[tuple[str, int]]) -> dict:
    """Crecimiento de la 2ª mitad de la ventana vs la 1ª mitad.

    `serie` = [(fecha_iso, seguidores), ...] ordenada. Se parte la ventana
    por tiempo (no por cantidad de puntos). Ratio >1.25 = acelera,
    <0.8 = enfría, medio = estable. Necesita ≥3 puntos.
    """
    if len(serie) < 3:
        return {"ratio": None, "estado": "sin datos"}

    t0, t1 = _fecha(serie[0][0]), _fecha(serie[-1][0])
    corte = t0 + (t1 - t0) / 2

    # último punto antes o en el corte = bisagra entre mitades
    bisagra = max((p for p in serie if _fecha(p[0]) <= corte), key=lambda p: _fecha(p[0]))
    delta_1 = bisagra[1] - serie[0][1]
    delta_2 = serie[-1][1] - bisagra[1]

    if delta_1 <= 0:
        # sin crecimiento en la 1ª mitad: cualquier subida posterior es aceleración
        if delta_2 > 0:
            return {"ratio": None, "estado": "acelera"}
        return {"ratio": None, "estado": "estable"}

    ratio = delta_2 / delta_1
    estado = "acelera" if ratio > 1.25 else ("enfria" if ratio < 0.8 else "estable")
    return {"ratio": ratio, "estado": estado}


def engagement_rate(videos: list[dict]) -> float | None:
    """Mediana por video de (likes + comentarios + shares) / views × 100."""
    tasas = [
        (v["likes"] + v["comments"] + v["shares"]) / v["views"] * 100
        for v in videos
        if v.get("views") and all(v.get(k) is not None for k in ("likes", "comments", "shares"))
    ]
    return mediana(tasas)


def velocidad_views(videos_inicio: list[dict], videos_fin: list[dict],
                    dias: float, followers: int | None) -> float | None:
    """Tracción: mediana de Δviews/día de los videos vistos en AMBOS snapshots,
    normalizada por cada 1.000 seguidores. None si no hay videos en común,
    días ≤ 0 o followers desconocidos (requiere ≥2 fotos del mismo video)."""
    if dias <= 0 or not followers:
        return None
    inicio_por_id = {v["id"]: v for v in videos_inicio if v.get("id")}
    deltas = [
        (v["views"] - inicio_por_id[v["id"]]["views"]) / dias
        for v in videos_fin
        if v.get("id") in inicio_por_id
        and v.get("views") is not None
        and inicio_por_id[v["id"]].get("views") is not None
    ]
    med = mediana(deltas)
    return med / followers * 1000 if med is not None else None


def cadencia_semanal(videos: list[dict], dias_ventana: float, fecha_fin: str) -> float | None:
    """Videos publicados dentro de la ventana, expresados por semana."""
    if dias_ventana <= 0:
        return None
    fin = _fecha(fecha_fin)
    inicio = fin.timestamp() - dias_ventana * 86400
    publicados = sum(
        1 for v in videos
        if v.get("postedAt") and inicio <= _fecha(v["postedAt"]).timestamp() <= fin.timestamp()
    )
    return publicados / (dias_ventana / 7)


def views_por_seguidor(videos: list[dict], followers: int | None) -> float | None:
    """Mediana de views_video / seguidores. Detecta cuentas que rinden
    sobre su tamaño (>1 = sus videos superan a su audiencia)."""
    if not followers:
        return None
    return mediana([v["views"] / followers for v in videos if v.get("views") is not None])


# ---------- eventos ----------

def detectar_breakouts(videos: list[dict], fecha_inicio: str, fecha_fin: str) -> list[dict]:
    """Videos con views ≥ 3 × la mediana de views de la cuenta, publicados
    dentro de la ventana. Devuelve [{id, caption, views, ratio, postedAt}]."""
    med = mediana([v["views"] for v in videos if v.get("views") is not None])
    if not med:
        return []
    ini, fin = _fecha(fecha_inicio), _fecha(fecha_fin)
    resultado = []
    for v in videos:
        if v.get("views") is None or not v.get("postedAt"):
            continue
        publicado = _fecha(v["postedAt"])
        if v["views"] >= 3 * med and ini <= publicado <= fin:
            resultado.append({
                "id": v["id"], "caption": v.get("caption"),
                "views": v["views"], "ratio": v["views"] / med,
                "postedAt": v["postedAt"],
            })
    return sorted(resultado, key=lambda b: b["ratio"], reverse=True)
