"""Carga y validación del perfil base (fuente única de verdad)."""
from functools import lru_cache
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
RUTA_PERFIL = RAIZ / "data" / "perfil.yaml"
RUTA_PERFIL_EJEMPLO = RAIZ / "data" / "perfil.example.yaml"
RUTA_RUBRICA = RAIZ / "data" / "rubrica.md"


@lru_cache(maxsize=1)
def cargar_perfil() -> dict:
    # Sin perfil propio (p. ej. recién clonado el repo) se usa el de ejemplo
    ruta = RUTA_PERFIL if RUTA_PERFIL.exists() else RUTA_PERFIL_EJEMPLO
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def recargar() -> dict:
    cargar_perfil.cache_clear()
    return cargar_perfil()


def indice_bullets() -> dict[str, dict]:
    """Mapa id_bullet -> datos del bullet + experiencia a la que pertenece."""
    indice = {}
    for exp in cargar_perfil()["experiencia"]:
        for b in exp["bullets"]:
            indice[b["id"]] = {**b, "experiencia_id": exp["id"], "empresa": exp["empresa"]}
    return indice


def validar_seleccion(variante: str, bullets: list[str]) -> list[str]:
    """Guardrail anti-invención: solo variantes y bullets que existen en el perfil."""
    errores = []
    variantes = cargar_perfil()["variantes"]
    if variante not in variantes:
        errores.append(f"Variante desconocida: {variante}. Opciones: {list(variantes)}")
    indice = indice_bullets()
    errores += [f"Bullet inexistente: {b}" for b in bullets if b not in indice]
    return errores


def rubrica() -> str:
    return RUTA_RUBRICA.read_text(encoding="utf-8")
