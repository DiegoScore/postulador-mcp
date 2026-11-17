import server
from postulador.cv import generar_cv
from postulador.perfil import validar_seleccion


def test_validar_seleccion_acepta_datos_validos():
    assert validar_seleccion("ai_engineer", ["a1", "g1"]) == []


def test_validar_seleccion_rechaza_bullet_inexistente():
    errores = validar_seleccion("ai_engineer", ["a1", "inventado"])
    assert any("inventado" in e for e in errores)


def test_validar_seleccion_rechaza_variante_inexistente():
    errores = validar_seleccion("astronauta", ["a1"])
    assert any("astronauta" in e for e in errores)


def test_save_evaluation_rechaza_empresa_excluida(evaluacion_valida):
    r = server.save_evaluation(**{**evaluacion_valida, "empresa": "ExampleCorp"})
    assert r["ok"] is False
    assert any("empresas_excluidas" in e for e in r["errores"])


def test_save_evaluation_rechaza_puntaje_fuera_de_rango(evaluacion_valida):
    for puntaje in (-1, 101):
        r = server.save_evaluation(**{**evaluacion_valida, "puntaje": puntaje})
        assert r["ok"] is False
        assert any("0 y 100" in e for e in r["errores"])


def test_save_evaluation_rechaza_bullets_inexistentes(evaluacion_valida):
    r = server.save_evaluation(**{**evaluacion_valida, "bullets": ["a1", "x9"]})
    assert r["ok"] is False


def test_save_evaluation_guarda_y_marca_umbral(evaluacion_valida):
    r = server.save_evaluation(**evaluacion_valida)
    assert r["ok"] is True and r["bajo_umbral"] is False
    r = server.save_evaluation(**{**evaluacion_valida, "cargo": "Otro", "puntaje": 10})
    assert r["bajo_umbral"] is True


def test_update_status_rechaza_estado_invalido(evaluacion_valida):
    id_ = server.save_evaluation(**evaluacion_valida)["id"]
    r = server.update_status(id_, "contratada_por_magia")
    assert r["ok"] is False
    assert server.get_application(id_)["estado"] == "nueva"


def test_update_status_rechaza_postulacion_inexistente():
    assert server.update_status(999, "aprobada")["ok"] is False


def test_build_cv_falla_si_no_esta_aprobada(evaluacion_valida, tmp_path):
    id_ = server.save_evaluation(**evaluacion_valida)["id"]
    r = server.build_cv(id_)
    assert r["ok"] is False
    assert "aprobada" in r["error"]
    assert not (tmp_path / "salidas").exists()


def test_build_cv_genera_docx_si_esta_aprobada(evaluacion_valida):
    id_ = server.save_evaluation(**evaluacion_valida)["id"]
    assert server.update_status(id_, "aprobada")["ok"] is True
    r = server.build_cv(id_)
    assert r["ok"] is True
    from pathlib import Path
    assert Path(r["ruta"]).exists() and r["ruta"].endswith(".docx")


def test_generar_cv_en_espanol_y_en_ingles():
    es = generar_cv("ai_engineer", ["a1", "a2", "g1"], "es", "cv_es")
    en = generar_cv("ai_engineer", ["a1", "a2", "g1"], "en", "cv_en")
    from pathlib import Path
    assert es["ok"] and en["ok"]
    assert Path(es["ruta"]).name == "cv_es.docx" and Path(es["ruta"]).stat().st_size > 0
    assert Path(en["ruta"]).name == "cv_en.docx" and Path(en["ruta"]).stat().st_size > 0


def test_generar_cv_rechaza_bullets_inexistentes():
    r = generar_cv("ai_engineer", ["inventado"], "es", "x")
    assert r["ok"] is False


def test_perfil_cae_al_ejemplo_si_no_existe_perfil_propio(tmp_path, monkeypatch):
    from postulador import perfil
    monkeypatch.setattr(perfil, "RUTA_PERFIL", tmp_path / "no_existe.yaml")
    perfil.cargar_perfil.cache_clear()
    assert perfil.cargar_perfil()["personal"]["nombre"] == "Ana Pérez"
