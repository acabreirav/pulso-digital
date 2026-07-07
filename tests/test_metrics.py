"""Tests de las fórmulas de métricas (CLAUDE.md §8).

Cada test fija por escrito una definición: si se cambia una fórmula,
primero se actualiza aquí (regla del §11).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from metrics import (
    aceleracion,
    cadencia_semanal,
    crecimiento_seguidores,
    detectar_breakouts,
    engagement_rate,
    mediana,
    velocidad_views,
    views_por_seguidor,
)


def video(id="v1", views=1000, likes=100, comments=10, shares=5,
          postedAt="2026-07-05T12:00:00Z", caption="..."):
    return {"id": id, "views": views, "likes": likes, "comments": comments,
            "shares": shares, "postedAt": postedAt, "caption": caption}


# ---------- mediana ----------

def test_mediana_impar_par_y_vacia():
    assert mediana([3, 1, 2]) == 2
    assert mediana([1, 2, 3, 4]) == 2.5
    assert mediana([]) is None
    assert mediana([None, 5, None]) == 5


def test_mediana_resiste_outliers_virales():
    # un video viral de 1M no debe arrastrar la métrica (por eso NO es promedio)
    assert mediana([100, 120, 110, 1_000_000]) == 115


# ---------- crecimiento ----------

def test_crecimiento_absoluto_y_porcentual():
    r = crecimiento_seguidores(1000, 1100)
    assert r["absoluto"] == 100
    assert r["porcentual"] == 10.0


def test_crecimiento_sin_datos_devuelve_none():
    assert crecimiento_seguidores(None, 1100) is None
    assert crecimiento_seguidores(1000, None) is None


# ---------- aceleración ----------

def test_aceleracion_umbral_acelera():
    # 1ª mitad: +100, 2ª mitad: +200 → ratio 2.0 > 1.25
    serie = [("2026-07-01T00:00Z", 1000), ("2026-07-04T00:00Z", 1100),
             ("2026-07-07T00:00Z", 1300)]
    r = aceleracion(serie)
    assert r["estado"] == "acelera" and r["ratio"] == 2.0


def test_aceleracion_umbral_enfria():
    # 1ª mitad: +200, 2ª mitad: +100 → ratio 0.5 < 0.8
    serie = [("2026-07-01T00:00Z", 1000), ("2026-07-04T00:00Z", 1200),
             ("2026-07-07T00:00Z", 1300)]
    assert aceleracion(serie)["estado"] == "enfria"


def test_aceleracion_estable_en_el_medio():
    # ratio 1.0: entre 0.8 y 1.25
    serie = [("2026-07-01T00:00Z", 1000), ("2026-07-04T00:00Z", 1100),
             ("2026-07-07T00:00Z", 1200)]
    assert aceleracion(serie)["estado"] == "estable"


def test_aceleracion_necesita_tres_puntos():
    serie = [("2026-07-01T00:00Z", 1000), ("2026-07-07T00:00Z", 1300)]
    assert aceleracion(serie)["estado"] == "sin datos"


# ---------- engagement ----------

def test_engagement_mediana_por_video():
    videos = [
        video(views=1000, likes=80, comments=15, shares=5),    # 10%
        video(views=2000, likes=30, comments=5, shares=5),     # 2%
        video(views=1000, likes=50, comments=5, shares=5),     # 6%
    ]
    assert engagement_rate(videos) == 6.0


def test_engagement_ignora_videos_sin_views():
    assert engagement_rate([video(views=0), video(views=None)]) is None


# ---------- velocidad de views ----------

def test_velocidad_normalizada_por_mil_seguidores():
    inicio = [video("a", views=1000), video("b", views=5000)]
    fin = [video("a", views=3000), video("b", views=7000)]
    # Δ por día: a=+1000/d, b=+1000/d (2 días) → mediana 1000/d
    # normalizada: 1000 / 10000 seguidores × 1000 = 100
    assert velocidad_views(inicio, fin, dias=2, followers=10_000) == 100


def test_velocidad_requiere_videos_en_comun():
    assert velocidad_views([video("a")], [video("b")], 2, 10_000) is None


def test_velocidad_requiere_dos_fotos():
    assert velocidad_views([], [video("a")], 0, 10_000) is None


# ---------- cadencia ----------

def test_cadencia_cuenta_solo_videos_de_la_ventana():
    videos = [
        video("a", postedAt="2026-07-06T00:00:00Z"),  # dentro
        video("b", postedAt="2026-07-03T00:00:00Z"),  # dentro
        video("c", postedAt="2026-06-01T00:00:00Z"),  # fuera
    ]
    # 2 videos en 7 días = 2 por semana
    assert cadencia_semanal(videos, 7, "2026-07-07T00:00:00Z") == 2.0


# ---------- views por seguidor ----------

def test_views_por_seguidor_es_mediana():
    videos = [video(views=500), video(views=1500), video(views=100_000)]
    assert views_por_seguidor(videos, 1000) == 1.5


# ---------- breakouts ----------

def test_breakout_regla_3x_mediana_dentro_de_ventana():
    videos = [
        video("v1", views=100), video("v2", views=110),
        video("v3", views=90, postedAt="2026-06-01T00:00:00Z"),
        video("viral", views=400, postedAt="2026-07-05T00:00:00Z"),  # 4× mediana
    ]
    r = detectar_breakouts(videos, "2026-07-01T00:00:00Z", "2026-07-07T00:00:00Z")
    assert [b["id"] for b in r] == ["viral"]
    assert r[0]["ratio"] == 400 / 105


def test_breakout_fuera_de_ventana_no_cuenta():
    videos = [video("v1", views=100), video("v2", views=110),
              video("viejo", views=900, postedAt="2026-01-01T00:00:00Z")]
    assert detectar_breakouts(videos, "2026-07-01T00:00:00Z",
                              "2026-07-07T00:00:00Z") == []
