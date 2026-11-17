"""Servidor MCP de postulación asistida.

El LLM (Claude u otro cliente MCP) hace el razonamiento; este servidor aporta
el perfil, la rúbrica, la cola de postulaciones y la generación de CVs, con
validaciones para que nada se invente.
"""
import os
from typing import Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from postulador import db
from postulador.cv import generar_cv
from postulador.perfil import cargar_perfil, recargar, rubrica, validar_seleccion

mcp = MCPServer(
    name="postulador",
    instructions=(
        "Asistente de postulación del candidato. Flujo: get_scoring_rubric y get_profile -> evaluar la oferta "
        "-> save_evaluation -> el usuario aprueba -> build_cv -> el usuario envía. "
        "Nunca inventes experiencia: usa solo el perfil. Nunca envíes postulaciones por tu cuenta."
    ),
)

Seccion = Literal["todo", "personal", "situacion_laboral", "idiomas", "educacion", "certificaciones",
                  "habilidades", "experiencia", "variantes", "respuestas_tipo", "filtros"]


@mcp.tool()
def get_profile(seccion: Seccion = "todo") -> dict:
    """Devuelve el perfil del candidato (o una sección). Es la única fuente de verdad."""
    perfil = recargar()
    return perfil if seccion == "todo" else {seccion: perfil[seccion]}


@mcp.tool()
def get_scoring_rubric() -> str:
    """Devuelve la rúbrica calibrada para puntuar ofertas y elegir variante y bullets."""
    return rubrica()


@mcp.tool()
def save_evaluation(
    empresa: str,
    cargo: str,
    puntaje: int,
    variante: str,
    bullets: list[str],
    calce: list[str],
    brechas: list[str],
    respuestas: dict[str, str] | None = None,
    url: str = "",
) -> dict:
    """Guarda la evaluación de una oferta en la cola (estado 'nueva').
    Valida que la variante y los ids de bullets existan en el perfil."""
    errores = validar_seleccion(variante, bullets)
    if not 0 <= puntaje <= 100:
        errores.append("El puntaje debe estar entre 0 y 100")
    excluidas = [e.lower() for e in cargar_perfil()["filtros"].get("empresas_excluidas", [])]
    if empresa.lower() in excluidas:
        errores.append(f"{empresa} está en empresas_excluidas")
    if errores:
        return {"ok": False, "errores": errores}
    id_ = db.guardar(dict(empresa=empresa, cargo=cargo, url=url, puntaje=puntaje, variante=variante,
                          bullets=bullets, calce=calce, brechas=brechas, respuestas=respuestas or {}))
    umbral = cargar_perfil()["filtros"]["umbral_score"]
    return {"ok": True, "id": id_, "bajo_umbral": puntaje < umbral, "umbral": umbral}


@mcp.tool()
def list_queue(estado: str | None = None, puntaje_min: int = 0) -> list[dict]:
    """Lista postulaciones, ordenadas por puntaje. Filtra por estado
    (nueva, aprobada, descartada, enviada, entrevista, rechazada, oferta)."""
    return [
        {k: p[k] for k in ("id", "empresa", "cargo", "puntaje", "variante", "estado", "url", "actualizada")}
        for p in db.listar(estado, puntaje_min)
    ]


@mcp.tool()
def get_application(id: int) -> dict:
    """Detalle completo de una postulación: calce, brechas, bullets y respuestas."""
    return db.obtener(id) or {"ok": False, "error": f"No existe la postulación {id}"}


@mcp.tool()
def update_status(id: int, estado: str, notas: str = "") -> dict:
    """Cambia el estado de una postulación. Solo pasar a 'aprobada' o 'enviada' si el usuario lo dijo."""
    try:
        return {"ok": True, "postulacion": db.actualizar_estado(id, estado, notas)}
    except ValueError as e:
        return {"ok": False, "error": str(e)}


@mcp.tool()
def build_cv(id: int, idioma: Literal["es", "en"] = "es") -> dict:
    """Genera el CV .docx adaptado a una postulación guardada (usa su variante y bullets).
    Requiere que la postulación esté 'aprobada'."""
    p = db.obtener(id)
    if not p:
        return {"ok": False, "error": f"No existe la postulación {id}"}
    if p["estado"] not in ("aprobada", "enviada"):
        return {"ok": False, "error": "La postulación debe estar aprobada por el usuario antes de generar el CV."}
    nombre_corto = cargar_perfil()["personal"]["nombre_corto"].replace(" ", "_")
    nombre = f"CV_{nombre_corto}_{p['empresa']}_{p['cargo']}_{idioma}"
    return generar_cv(p["variante"], p["bullets"], idioma, nombre)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    """Healthcheck para Docker (solo en modo HTTP)."""
    return JSONResponse({"status": "ok"})


def main() -> None:
    transporte = os.getenv("MCP_TRANSPORT", "stdio")
    if transporte == "stdio":
        mcp.run()
        return
    hosts = [h.strip() for h in os.getenv("MCP_ALLOWED_HOSTS", "localhost:*,127.0.0.1:*").split(",") if h.strip()]
    mcp.run(
        "streamable-http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_PORT", "8000")),
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=hosts),
    )


if __name__ == "__main__":
    main()
