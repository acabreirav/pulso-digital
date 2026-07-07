"""Fase 0 — "Hola mundo" del proyecto.

Verifica que el entorno local está listo antes de escribir el pipeline:
Python correcto, dependencias instaladas, estructura de carpetas y config presentes.
No llama a ninguna API ni gasta nada. Correr con:  python src/check_env.py
"""

import json
import sys
from pathlib import Path

# Raíz del repo = carpeta padre de src/
ROOT = Path(__file__).resolve().parent.parent

OK = "  [ok] "
FAIL = "  [FALTA] "


def check(descripcion: str, condicion: bool) -> bool:
    print((OK if condicion else FAIL) + descripcion)
    return condicion


def main() -> int:
    print("Radar de Tracción — verificación del entorno (Fase 0)\n")
    resultados = []

    # 1. Versión de Python
    resultados.append(check(
        f"Python {sys.version_info.major}.{sys.version_info.minor} (se requiere 3.10+)",
        sys.version_info >= (3, 10),
    ))

    # 2. Dependencias instaladas
    for modulo in ("requests", "dotenv"):
        try:
            __import__(modulo)
            resultados.append(check(f"dependencia '{modulo}' instalada", True))
        except ImportError:
            resultados.append(check(
                f"dependencia '{modulo}' instalada — corre: pip install -r requirements.txt",
                False,
            ))

    # 3. Estructura de carpetas
    for carpeta in ("config", "src", "data/snapshots", "docs", "tests"):
        resultados.append(check(f"carpeta {carpeta}/", (ROOT / carpeta).is_dir()))

    # 4. Lista de cuentas legible y con contenido
    ruta_cuentas = ROOT / "config" / "accounts.json"
    try:
        cuentas = json.loads(ruta_cuentas.read_text())["accounts"]
        resultados.append(check(
            f"config/accounts.json legible ({len(cuentas)} cuentas: {', '.join(cuentas)})",
            1 <= len(cuentas),
        ))
    except (OSError, KeyError, json.JSONDecodeError) as e:
        resultados.append(check(f"config/accounts.json legible — error: {e}", False))

    # 5. El token NO es requisito en Fase 0, solo avisamos su estado
    from dotenv import load_dotenv
    import os
    load_dotenv(ROOT / ".env")
    if os.getenv("APIFY_TOKEN"):
        print(OK + "APIFY_TOKEN encontrado en .env (listo para la Fase 1)")
    else:
        print("  [info] APIFY_TOKEN aún no configurado — copia .env.example a .env"
              " y pon tu token. Solo hace falta para la Fase 1.")

    if all(resultados):
        print("\nTodo listo. Fase 0 completa: el entorno funciona.")
        return 0
    print("\nHay pendientes marcados como [FALTA]. Resuélvelos antes de seguir.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
