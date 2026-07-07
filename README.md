# Radar de Tracción — monitor de cuentas TikTok

Panel que se regenera periódicamente con métricas de crecimiento y tracción de un
conjunto de cuentas públicas de TikTok, para detectar cuáles ganan momentum y por qué.

**La idea central:** TikTok no entrega histórico de cuentas ajenas, solo fotos del momento.
Las tasas de crecimiento las generamos nosotros: `snapshot → guardar → comparar contra la
foto anterior → reportar el delta`. El repo mismo es la base de datos (snapshots JSON en
`data/snapshots/`).

> La memoria completa del proyecto (arquitectura, decisiones, métricas, plan por fases)
> vive en [`CLAUDE.md`](CLAUDE.md).

## Cómo correr en local

```bash
# 1. Crear y activar un entorno virtual (aísla las dependencias de este proyecto)
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar que todo está en orden (no llama a ninguna API)
python src/check_env.py

# 4. (Fase 1) Configurar el token de Apify
cp .env.example .env             # luego edita .env y pega tu APIFY_TOKEN
```

## Estructura

```
config/accounts.json    # lista de handles a monitorear (edítala tú)
src/                    # pipeline en Python (fetch, métricas, reporte)
data/snapshots/         # histórico: un JSON por corrida — la "base de datos"
docs/                   # dashboard estático que servirá GitHub Pages
tests/                  # tests de las fórmulas de métricas
```

## Estado

Fase 0 (setup local) completa. Siguiente: Fase 1 — fetch mínimo de 2-3 cuentas
vía Apify (requiere confirmar costo antes de correr). Ver plan completo en `CLAUDE.md` §12.
