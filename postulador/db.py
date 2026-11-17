"""Cola de postulaciones en SQLite."""
import json
import sqlite3
from datetime import datetime

from .perfil import RAIZ

RUTA_DB = RAIZ / "data" / "postulaciones.db"
ESTADOS = ["nueva", "aprobada", "descartada", "enviada", "entrevista", "rechazada", "oferta"]
CAMPOS_JSON = ("bullets", "calce", "brechas", "respuestas")


def conexion() -> sqlite3.Connection:
    con = sqlite3.connect(RUTA_DB)
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE IF NOT EXISTS postulaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            cargo TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT '',
            puntaje INTEGER NOT NULL,
            variante TEXT NOT NULL,
            bullets TEXT NOT NULL,
            calce TEXT, brechas TEXT, respuestas TEXT,
            estado TEXT NOT NULL DEFAULT 'nueva',
            notas TEXT NOT NULL DEFAULT '',
            creada TEXT NOT NULL,
            actualizada TEXT NOT NULL,
            UNIQUE(empresa, cargo, url)
        )"""
    )
    return con


def _fila(r: sqlite3.Row) -> dict:
    d = dict(r)
    for k in CAMPOS_JSON:
        d[k] = json.loads(d[k]) if d[k] else None
    return d


def guardar(ev: dict) -> int:
    """Inserta o actualiza (misma empresa + cargo + url) y devuelve el id."""
    ahora = datetime.now().isoformat(timespec="seconds")
    valores = {k: json.dumps(ev.get(k) or ([] if k != "respuestas" else {}), ensure_ascii=False) for k in CAMPOS_JSON}
    with conexion() as con:
        cur = con.execute(
            """INSERT INTO postulaciones
               (empresa, cargo, url, puntaje, variante, bullets, calce, brechas, respuestas, creada, actualizada)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(empresa, cargo, url) DO UPDATE SET
                 puntaje=excluded.puntaje, variante=excluded.variante, bullets=excluded.bullets,
                 calce=excluded.calce, brechas=excluded.brechas, respuestas=excluded.respuestas,
                 actualizada=excluded.actualizada
               RETURNING id""",
            (ev["empresa"], ev["cargo"], ev.get("url") or "", ev["puntaje"], ev["variante"],
             valores["bullets"], valores["calce"], valores["brechas"], valores["respuestas"], ahora, ahora),
        )
        return cur.fetchone()[0]


def listar(estado: str | None = None, puntaje_min: int = 0) -> list[dict]:
    sql, params = "SELECT * FROM postulaciones WHERE puntaje >= ?", [puntaje_min]
    if estado:
        sql += " AND estado = ?"
        params.append(estado)
    sql += " ORDER BY puntaje DESC, creada DESC"
    with conexion() as con:
        return [_fila(r) for r in con.execute(sql, params)]


def obtener(id_: int) -> dict | None:
    with conexion() as con:
        r = con.execute("SELECT * FROM postulaciones WHERE id = ?", (id_,)).fetchone()
    return _fila(r) if r else None


def actualizar_estado(id_: int, estado: str, notas: str = "") -> dict:
    if estado not in ESTADOS:
        raise ValueError(f"Estado inválido. Opciones: {ESTADOS}")
    if not obtener(id_):
        raise ValueError(f"No existe la postulación {id_}")
    ahora = datetime.now().isoformat(timespec="seconds")
    with conexion() as con:
        con.execute(
            "UPDATE postulaciones SET estado=?, notas=TRIM(notas || ' ' || ?), actualizada=? WHERE id=?",
            (estado, notas, ahora, id_),
        )
    return obtener(id_)
