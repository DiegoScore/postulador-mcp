"""Genera un CV .docx de una columna (amigable con ATS) a partir del perfil.

Solo reordena y selecciona contenido existente: nunca agrega texto nuevo.
"""
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from .perfil import RAIZ, cargar_perfil, indice_bullets, validar_seleccion

CARPETA_SALIDA = RAIZ / "salidas"
ACENTO = RGBColor(0x1F, 0x3A, 0x5F)
GRIS = RGBColor(0x55, 0x55, 0x55)

TEXTOS = {
    "es": {"resumen": "Resumen", "exp": "Experiencia", "edu": "Educación", "hab": "Habilidades",
           "cert": "Certificaciones", "idiomas": "Idiomas", "presente": "presente",
           "meses": "ene feb mar abr may jun jul ago sep oct nov dic"},
    "en": {"resumen": "Summary", "exp": "Experience", "edu": "Education", "hab": "Skills",
           "cert": "Certifications", "idiomas": "Languages", "presente": "present",
           "meses": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec"},
}


def _fecha(valor: str, idioma: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}", str(valor)):
        return TEXTOS[idioma]["presente"]
    anio, mes = str(valor).split("-")
    return f"{TEXTOS[idioma]['meses'].split()[int(mes) - 1]} {anio}"


def _linea_inferior(parrafo) -> None:
    pPr = parrafo._p.get_or_add_pPr()
    borde = OxmlElement("w:pBdr")
    abajo = OxmlElement("w:bottom")
    for k, v in {"w:val": "single", "w:sz": "6", "w:space": "1", "w:color": "1F3A5F"}.items():
        abajo.set(qn(k), v)
    borde.append(abajo)
    pPr.append(borde)


def _titulo_seccion(doc, texto: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(texto.upper())
    r.bold, r.font.size, r.font.color.rgb = True, Pt(11), ACENTO
    _linea_inferior(p)


def _parrafo(doc, texto: str = "", tam: float = 10, despues: float = 2):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(despues)
    if texto:
        p.add_run(texto).font.size = Pt(tam)
    return p


def generar_cv(variante: str, bullets: list[str], idioma: str = "es", nombre_archivo: str | None = None) -> dict:
    errores = validar_seleccion(variante, bullets)
    if idioma not in TEXTOS:
        errores.append("Idioma debe ser 'es' o 'en'")
    indice = indice_bullets()
    if idioma == "en":
        sin_traduccion = [b for b in bullets if b in indice and not indice[b].get("en")]
        if sin_traduccion:
            errores.append(f"Bullets sin versión 'en' en perfil.yaml: {sin_traduccion}")
    if errores:
        return {"ok": False, "errores": errores}

    perfil = cargar_perfil()
    t = TEXTOS[idioma]
    var = perfil["variantes"][variante]
    p_ = perfil["personal"]

    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(1.3)
        s.left_margin = s.right_margin = Cm(1.8)
    estilo = doc.styles["Normal"]
    estilo.font.name, estilo.font.size = "Calibri", Pt(10)

    # Encabezado
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(p_["nombre"])
    r.bold, r.font.size, r.font.color.rgb = True, Pt(18), ACENTO
    p = _parrafo(doc, despues=1)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(var["titulo_en"] if idioma == "en" else var["titulo"])
    r.font.size, r.font.color.rgb = Pt(11.5), GRIS
    contacto = " | ".join(filter(None, [
        f"{p_['ciudad']}, {p_['pais']}", p_["email"], p_["telefono"],
        *(p_["links"].get(k, "").replace("https://", "").rstrip("/") for k in ("linkedin", "github", "portafolio")),
    ]))
    p = _parrafo(doc, contacto, tam=9, despues=4)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    _titulo_seccion(doc, t["resumen"])
    _parrafo(doc, " ".join((var["resumen_en"] if idioma == "en" else var["resumen_es"]).split()), despues=2)

    # Experiencia: solo las que tienen bullets elegidos, en orden cronológico inverso;
    # dentro de cada experiencia se respeta el orden elegido.
    _titulo_seccion(doc, t["exp"])
    advertencias = []
    for exp in perfil["experiencia"]:  # el YAML ya está en orden cronológico inverso
        elegidos = [b for b in bullets if indice[b]["experiencia_id"] == exp["id"]]
        if not elegidos:
            continue
        p = _parrafo(doc, despues=0)
        p.paragraph_format.space_before = Pt(5)
        r = p.add_run(exp["cargo_en"] if idioma == "en" else exp["cargo"])
        r.bold, r.font.size = True, Pt(10.5)
        etiqueta_tipo = f" ({exp['tipo']})" if exp.get("tipo") in ("freelance", "proyecto de investigación") else ""
        p.add_run(f" — {exp['empresa']}{etiqueta_tipo}").font.size = Pt(10.5)
        _parrafo(doc, f"{_fecha(exp['inicio'], idioma)} – {_fecha(exp['fin'], idioma)}", tam=9, despues=2).runs[0].font.color.rgb = GRIS
        for b in elegidos:
            datos = indice[b]
            bp = doc.add_paragraph(style="List Bullet")
            bp.paragraph_format.space_after = Pt(1)
            bp.add_run(datos["en"] if idioma == "en" else datos["es"]).font.size = Pt(10)
            if datos.get("revisar_metrica"):
                advertencias.append(f"{b}: tiene una métrica marcada para revisar; asegúrate de poder defenderla.")

    _titulo_seccion(doc, t["edu"])
    for e in perfil["educacion"]:
        p = _parrafo(doc, despues=1)
        r = p.add_run(e["titulo_en"] if idioma == "en" else e["titulo"])
        r.bold = True
        p.add_run(f" — {e['institucion']} ({e['inicio'][:4]}–{e['fin'][:4]})")

    _titulo_seccion(doc, t["hab"])
    nombres = {"lenguajes": "Lenguajes", "ia_ml": "IA / ML", "web": "Web", "datos": "Datos",
               "cloud_devops": "Cloud / DevOps"}
    for clave, etiqueta in nombres.items():
        p = _parrafo(doc, despues=1)
        p.add_run(f"{etiqueta}: ").bold = True
        p.add_run(", ".join(perfil["habilidades"][clave].keys()))
    p = _parrafo(doc, despues=1)
    p.add_run(f"{t['idiomas']}: ").bold = True
    p.add_run(", ".join(f"{i['idioma']} ({i['nivel']})" for i in perfil["idiomas"]))

    certs = [c["nombre"] for c in perfil.get("certificaciones", [])]
    if certs:
        _titulo_seccion(doc, t["cert"])
        for c in certs:
            doc.add_paragraph(c, style="List Bullet").paragraph_format.space_after = Pt(1)


    CARPETA_SALIDA.mkdir(exist_ok=True)
    nombre = nombre_archivo or f"CV_{p_['nombre_corto'].replace(' ', '_')}_{variante}_{idioma}"
    ruta = CARPETA_SALIDA / f"{re.sub(r'[^A-Za-z0-9_-]', '_', nombre)}.docx"
    doc.save(ruta)
    return {"ok": True, "ruta": str(ruta), "advertencias": advertencias}
