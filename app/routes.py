"""Capa web: sesion, CSRF, permisos de entrada y vistas. Las reglas viven en services.py."""
import hmac
import secrets

from flask import (Blueprint, abort, current_app, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from . import services
from .db import get_db
from .services import ServiceError

bp = Blueprint("web", __name__)

_DUMMY_HASH = generate_password_hash("no-es-una-cuenta")
PUBLIC_ENDPOINTS = {"web.login", "static"}


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


@bp.app_context_processor
def inject():
    return {"csrf_token": csrf_token, "user": g.get("user"), "services": services}


@bp.before_app_request
def load_user_and_protect():
    g.user = None
    uid = session.get("user_id")
    if uid is not None:
        row = get_db().execute("SELECT * FROM users WHERE id = ? AND active = 1", (uid,)).fetchone()
        if row is None:
            session.clear()
        else:
            g.user = row
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf", "")
        # Un token ausente nunca es valido (evita que "" == "" pase la comparacion).
        if not expected or not hmac.compare_digest(sent, expected):
            abort(400, "Token CSRF invalido.")
    if g.user is None and request.endpoint not in PUBLIC_ENDPOINTS:
        return redirect(url_for("web.login"))


@bp.errorhandler(ServiceError)
def service_error(err):
    return render_template("error.html", message=err.message, status=err.status), err.status


@bp.app_errorhandler(400)
@bp.app_errorhandler(404)
def http_error(err):
    return render_template("error.html", message=getattr(err, "description", "Error"),
                           status=err.code), err.code


def now():
    return current_app.config["CLOCK"]()


# ------------------------------------------------------------------ sesion
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("usuario", "").strip()
        password = request.form.get("clave", "")
        row = get_db().execute("SELECT * FROM users WHERE username = ? AND active = 1",
                               (username,)).fetchone()
        ok = check_password_hash(row["password_hash"] if row else _DUMMY_HASH, password)
        if row and ok:
            session.clear()
            session["user_id"] = row["id"]
            csrf_token()  # token nuevo para la sesion autenticada
            return redirect(url_for("web.incidents"))
        return render_template("login.html", error="Usuario o clave incorrectos."), 401
    return render_template("login.html", error=None)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("web.login"))


@bp.get("/")
def index():
    return redirect(url_for("web.incidents"))


# ------------------------------------------------------------------ RF05 consulta
@bp.get("/incidencias")
def incidents():
    status = request.args.get("estado", "").strip() or None
    priority = request.args.get("prioridad", "").strip() or None
    rows = services.list_incidents(get_db(), g.user, status, priority)
    return render_template("incidents.html", rows=rows, status=status, priority=priority)


@bp.get("/incidencias/<int:incident_id>")
def detail(incident_id):
    inc, events, solutions, closures, technician = services.get_detail(get_db(), g.user, incident_id)
    techs = services.active_technicians(get_db()) if g.user["role"] == "COORDINADOR" else []
    return render_template("detail.html", inc=inc, events=events, solutions=solutions,
                           closures=closures, technician=technician, techs=techs)


@bp.get("/tablero")
def dashboard():
    return render_template("dashboard.html", d=services.dashboard(get_db(), g.user))


# ------------------------------------------------------------------ RF01
@bp.route("/incidencias/nueva", methods=["GET", "POST"])
def new_incident():
    if g.user["role"] != "SOLICITANTE":
        abort_service(403, "Solo el solicitante registra incidencias.")
    if request.method == "POST":
        try:
            inc_id = services.create_incident(get_db(), g.user, request.form, now())
        except ServiceError as err:
            return render_template("new.html", error=err.message, form=request.form), err.status
        return redirect(url_for("web.detail", incident_id=inc_id))
    return render_template("new.html", error=None, form={})


def abort_service(status, message):
    raise ServiceError(status, message)


# ------------------------------------------------------------------ transiciones
def _after(incident_id):
    return redirect(url_for("web.detail", incident_id=incident_id))


@bp.post("/incidencias/<int:incident_id>/asignar")
def assign(incident_id):
    services.assign(get_db(), g.user, incident_id, request.form.get("tecnico_id"), now())
    return _after(incident_id)


@bp.post("/incidencias/<int:incident_id>/iniciar")
def start(incident_id):
    services.start(get_db(), g.user, incident_id, now())
    return _after(incident_id)


@bp.post("/incidencias/<int:incident_id>/solucion")
def solve(incident_id):
    services.solve(get_db(), g.user, incident_id, request.form.get("solucion"), now())
    return _after(incident_id)


@bp.post("/incidencias/<int:incident_id>/confirmar")
def confirm(incident_id):
    services.confirm(get_db(), g.user, incident_id, now())
    return _after(incident_id)


@bp.post("/incidencias/<int:incident_id>/rechazar")
def reject(incident_id):
    services.reject(get_db(), g.user, incident_id, request.form.get("motivo"), now())
    return _after(incident_id)


@bp.post("/incidencias/<int:incident_id>/reabrir")
def reopen(incident_id):
    services.reopen(get_db(), g.user, incident_id, request.form.get("motivo"), now())
    return _after(incident_id)
