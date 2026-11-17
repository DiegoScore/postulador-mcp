"""Fixtures: perfil de ejemplo, base SQLite temporal y carpeta de salida temporal."""
import pytest

from postulador import cv, db, perfil


@pytest.fixture(autouse=True)
def entorno_aislado(tmp_path, monkeypatch):
    """Nunca toca data/perfil.yaml, data/postulaciones.db ni salidas/ reales."""
    monkeypatch.setattr(perfil, "RUTA_PERFIL", perfil.RUTA_PERFIL_EJEMPLO)
    monkeypatch.setattr(db, "RUTA_DB", tmp_path / "postulaciones.db")
    monkeypatch.setattr(cv, "CARPETA_SALIDA", tmp_path / "salidas")
    perfil.cargar_perfil.cache_clear()
    yield
    perfil.cargar_perfil.cache_clear()


@pytest.fixture
def evaluacion_valida():
    return dict(
        empresa="Acme", cargo="AI Engineer", puntaje=80, variante="ai_engineer",
        bullets=["a1", "a2"], calce=["LLMs -> a1"], brechas=["GCP"],
    )
