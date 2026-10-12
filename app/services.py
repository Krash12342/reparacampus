"""Logica de negocio de ReparaCampus. Todas las reglas se ejecutan en el servidor.

Orden de comprobaciones en cada operacion: rol/pertenencia (403) -> existencia (404)
-> estado (409) -> validacion de entradas (400). Una operacion rechazada no escribe nada.
"""
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from .db import transaction

LOCATIONS = ("LAB-01", "AULA-201", "BIB-01")
CATEGORIES = ("ELECTRICIDAD", "HIDRAULICA", "MOBILIARIO", "TIC")
IMPACTS = ("BAJO", "ALTO")
PRIORITIES = ("CRITICA", "ALTA", "NORMAL")
STATUSES = ("REGISTRADA", "ASIGNADA", "EN_ATENCION", "PENDIENTE_VALIDACION", "CERRADA")
REOPEN_WINDOW = timedelta(hours=48)

DESC_LIMITS = (20, 500)
SOLUTION_LIMITS = (20, 800)
REASON_LIMITS = (10, 300)


class ServiceError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def iso(dt):
    return dt.isoformat(timespec="seconds")


def compute_priority(risk, impact):
    if risk:
        return "CRITICA"
    return "ALTA" if impact == "ALTO" else "NORMAL"


def _text(value, label, limits):
    """Aplica strip y valida longitud (los limites se cuentan tras retirar espacios externos)."""
    value = (value or "").strip()
    lo, hi = limits
    if not (lo <= len(value) <= hi):
        raise ServiceError(400, f"{label} debe tener entre {lo} y {hi} caracteres.")
    return value


def _require_role(user, role):
    if user["role"] != role:
        raise ServiceError(403, "No tiene permiso para esta operacion.")


def _incident(db, incident_id):
    row = db.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    if row is None:
        raise ServiceError(404, "La incidencia no existe.")
    return row


def can_view(user, inc):
    if user["role"] == "COORDINADOR":
        return True
    if user["role"] == "SOLICITANTE":
        return inc["author_id"] == user["id"]
    return inc["technician_id"] == user["id"]


def _event(db, inc_id, actor_id, now, action, from_status, to_status, detail=None):
    db.execute(
        "INSERT INTO events (incident_id, actor_id, at, action, from_status, to_status, detail) "
        "VALUES (?,?,?,?,?,?,?)",
        (inc_id, actor_id, iso(now), action, from_status, to_status, detail),
    )


def _set_status(db, inc_id, new_status, **extra):
    sets = ["status = ?"] + [f"{k} = ?" for k in extra]
    db.execute(f"UPDATE incidents SET {', '.join(sets)} WHERE id = ?",
               (new_status, *extra.values(), inc_id))


# --------------------------------------------------------------------- RF01
def parse_risk(raw):
    raw = (raw or "").strip().lower()
    if raw == "true":
        return 1
    if raw == "false":
        return 0
    raise ServiceError(400, "El riesgo para personas debe ser true o false.")


def create_incident(db, user, form, now):
    _require_role(user, "SOLICITANTE")
    location = (form.get("ubicacion") or "").strip()
    category = (form.get("categoria") or "").strip()
    impact = (form.get("impacto") or "").strip()
    if location not in LOCATIONS:
        raise ServiceError(400, "Ubicacion invalida.")
    if category not in CATEGORIES:
        raise ServiceError(400, "Categoria invalida.")
    if impact not in IMPACTS:
        raise ServiceError(400, "Impacto invalido (BAJO o ALTO).")
    risk = parse_risk(form.get("riesgo"))
    description = _text(form.get("descripcion"), "La descripcion", DESC_LIMITS)
    priority = compute_priority(risk, impact)

    with transaction(db):
        next_n = db.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM incidents").fetchone()[0]
        code = f"INC-{next_n:04d}"
        cur = db.execute(
            "INSERT INTO incidents (code, location, category, description, impact, risk, priority, "
            "status, author_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (code, location, category, description, impact, risk, priority,
             "REGISTRADA", user["id"], iso(now)),
        )
        inc_id = cur.lastrowid
        _event(db, inc_id, user["id"], now, "CREAR", None, "REGISTRADA",
               f"prioridad={priority}")
    return inc_id


# --------------------------------------------------------------------- RF02
def assign(db, user, incident_id, technician_id, now):
    _require_role(user, "COORDINADOR")
    with transaction(db):
        inc = _incident(db, incident_id)
        if inc["status"] != "REGISTRADA":
            raise ServiceError(409, "Solo se asigna una incidencia REGISTRADA (sin reasignacion).")
        try:
            technician_id = int(technician_id)
        except (TypeError, ValueError):
            raise ServiceError(400, "Tecnico invalido.")
        tech = db.execute("SELECT * FROM users WHERE id = ?", (technician_id,)).fetchone()
        if tech is None or tech["role"] != "TECNICO" or not tech["active"]:
            raise ServiceError(400, "El tecnico debe existir y estar activo.")
        _set_status(db, inc["id"], "ASIGNADA", technician_id=tech["id"])
        _event(db, inc["id"], user["id"], now, "ASIGNAR", "REGISTRADA", "ASIGNADA",
               f"tecnico={tech['username']}")


# --------------------------------------------------------------------- RF03
def _assigned_technician(db, user, incident_id):
    _require_role(user, "TECNICO")
    inc = _incident(db, incident_id)
    if inc["technician_id"] != user["id"]:
        raise ServiceError(403, "La incidencia no esta asignada a este tecnico.")
    return inc


def start(db, user, incident_id, now):
    _require_role(user, "TECNICO")
    with transaction(db):
        inc = _assigned_technician(db, user, incident_id)
        if inc["status"] != "ASIGNADA":
            raise ServiceError(409, "Solo se inicia una incidencia ASIGNADA.")
        _set_status(db, inc["id"], "EN_ATENCION")
        _event(db, inc["id"], user["id"], now, "INICIAR", "ASIGNADA", "EN_ATENCION")


def solve(db, user, incident_id, text, now):
    _require_role(user, "TECNICO")
    with transaction(db):
        inc = _assigned_technician(db, user, incident_id)
        if inc["status"] != "EN_ATENCION":
            raise ServiceError(409, "Solo se registra solucion en una incidencia EN_ATENCION.")
        text = _text(text, "La solucion", SOLUTION_LIMITS)
        db.execute("INSERT INTO solutions (incident_id, technician_id, text, created_at) "
                   "VALUES (?,?,?,?)", (inc["id"], user["id"], text, iso(now)))
        _set_status(db, inc["id"], "PENDIENTE_VALIDACION")
        _event(db, inc["id"], user["id"], now, "REGISTRAR_SOLUCION", "EN_ATENCION",
               "PENDIENTE_VALIDACION", text)


# --------------------------------------------------------------------- RF04
def _owned(db, user, incident_id):
    _require_role(user, "SOLICITANTE")
    inc = _incident(db, incident_id)
    if inc["author_id"] != user["id"]:
        raise ServiceError(403, "Solo el solicitante duenio puede realizar esta operacion.")
    return inc


def confirm(db, user, incident_id, now):
    _require_role(user, "SOLICITANTE")
    with transaction(db):
        inc = _owned(db, user, incident_id)
        if inc["status"] != "PENDIENTE_VALIDACION":
            raise ServiceError(409, "Solo se confirma una solucion PENDIENTE_VALIDACION.")
        db.execute("INSERT INTO closures (incident_id, closed_by, closed_at) VALUES (?,?,?)",
                   (inc["id"], user["id"], iso(now)))
        _set_status(db, inc["id"], "CERRADA", last_closed_at=iso(now))
        _event(db, inc["id"], user["id"], now, "CERRAR", "PENDIENTE_VALIDACION", "CERRADA")


def reject(db, user, incident_id, reason, now):
    _require_role(user, "SOLICITANTE")
    with transaction(db):
        inc = _owned(db, user, incident_id)
        if inc["status"] != "PENDIENTE_VALIDACION":
            raise ServiceError(409, "Solo se rechaza una solucion PENDIENTE_VALIDACION.")
        reason = _text(reason, "El motivo", REASON_LIMITS)
        _set_status(db, inc["id"], "EN_ATENCION")  # mismo tecnico; soluciones se conservan
        _event(db, inc["id"], user["id"], now, "RECHAZAR", "PENDIENTE_VALIDACION",
               "EN_ATENCION", reason)


def reopen(db, user, incident_id, reason, now):
    _require_role(user, "SOLICITANTE")
    with transaction(db):
        inc = _owned(db, user, incident_id)
        if inc["status"] != "CERRADA":
            raise ServiceError(409, "Solo se reabre una incidencia CERRADA.")
        closed_at = datetime.fromisoformat(inc["last_closed_at"])
        if now - closed_at > REOPEN_WINDOW:  # <= 48 h se acepta
            raise ServiceError(409, "El plazo de 48 horas para reabrir ha vencido.")
        reason = _text(reason, "El motivo", REASON_LIMITS)
        _set_status(db, inc["id"], "EN_ATENCION")
        _event(db, inc["id"], user["id"], now, "REABRIR", "CERRADA", "EN_ATENCION", reason)


# --------------------------------------------------------------------- RF05
def list_incidents(db, user, status=None, priority=None):
    if status and status not in STATUSES:
        raise ServiceError(400, "Filtro de estado invalido.")
    if priority and priority not in PRIORITIES:
        raise ServiceError(400, "Filtro de prioridad invalido.")
    sql, args = "SELECT i.*, a.username AS author_name FROM incidents i " \
                "JOIN users a ON a.id = i.author_id WHERE 1=1", []
    if user["role"] == "SOLICITANTE":
        sql += " AND i.author_id = ?"; args.append(user["id"])
    elif user["role"] == "TECNICO":
        sql += " AND i.technician_id = ?"; args.append(user["id"])
    if status:
        sql += " AND i.status = ?"; args.append(status)
    if priority:
        sql += " AND i.priority = ?"; args.append(priority)
    return db.execute(sql + " ORDER BY i.id DESC", args).fetchall()


def get_detail(db, user, incident_id):
    inc = _incident(db, incident_id)
    if not can_view(user, inc):
        raise ServiceError(403, "No tiene permiso para ver esta incidencia.")
    events = db.execute(
        "SELECT e.*, u.username AS actor FROM events e JOIN users u ON u.id = e.actor_id "
        "WHERE e.incident_id = ? ORDER BY e.id", (incident_id,)).fetchall()
    solutions = db.execute("SELECT * FROM solutions WHERE incident_id = ? ORDER BY id",
                           (incident_id,)).fetchall()
    closures = db.execute("SELECT * FROM closures WHERE incident_id = ? ORDER BY id",
                          (incident_id,)).fetchall()
    technician = None
    if inc["technician_id"]:
        technician = db.execute("SELECT username FROM users WHERE id = ?",
                                (inc["technician_id"],)).fetchone()["username"]
    return inc, events, solutions, closures, technician


def active_technicians(db):
    return db.execute("SELECT id, username, full_name FROM users "
                      "WHERE role = 'TECNICO' AND active = 1 ORDER BY id").fetchall()


def format_percent(closed, total):
    if total == 0:
        return "0,0 %"
    pct = (Decimal(closed) * 100 / Decimal(total)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{pct}".replace(".", ",") + " %"


def dashboard(db, user):
    _require_role(user, "COORDINADOR")
    by_status = {s: 0 for s in STATUSES}
    by_priority = {p: 0 for p in PRIORITIES}
    for r in db.execute("SELECT status, COUNT(*) n FROM incidents GROUP BY status"):
        by_status[r["status"]] = r["n"]
    for r in db.execute("SELECT priority, COUNT(*) n FROM incidents GROUP BY priority"):
        by_priority[r["priority"]] = r["n"]
    critical_open = db.execute(
        "SELECT * FROM incidents WHERE priority = 'CRITICA' AND status <> 'CERRADA' ORDER BY id"
    ).fetchall()
    total = sum(by_status.values())
    return {
        "by_status": by_status, "by_priority": by_priority, "critical_open": critical_open,
        "total": total, "closed": by_status["CERRADA"],
        "closure_pct": format_percent(by_status["CERRADA"], total),
    }
