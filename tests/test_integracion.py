"""Pruebas de integracion: flujos completos contra SQLite real (archivo en disco)."""
import pytest

from .helpers import hours, register

pytestmark = pytest.mark.integration


def _historial(env, inc):
    return [(e["action"], e["from_status"], e["to_status"]) for e in
            env.q("SELECT * FROM events WHERE incident_id=? ORDER BY id", (inc,))]


def test_flujo_de_cierre(env):
    """INT-01: registrar -> asignar -> iniciar -> solucion -> confirmar."""
    inc = register(env, riesgo="true")
    coord, tec, sol = env.login("coord1"), env.login("tec1"), env.login("sol1")
    assert coord.post(f"/incidencias/{inc}/asignar", {"tecnico_id": env.uid("tec1")}).status_code == 302
    assert tec.post(f"/incidencias/{inc}/iniciar").status_code == 302
    assert tec.post(f"/incidencias/{inc}/solucion",
                    {"solucion": "Se aislo el circuito y se cambio el breaker"}).status_code == 302
    assert sol.post(f"/incidencias/{inc}/confirmar").status_code == 302
    assert env.state(inc)["status"] == "CERRADA"
    assert _historial(env, inc) == [
        ("CREAR", None, "REGISTRADA"), ("ASIGNAR", "REGISTRADA", "ASIGNADA"),
        ("INICIAR", "ASIGNADA", "EN_ATENCION"),
        ("REGISTRAR_SOLUCION", "EN_ATENCION", "PENDIENTE_VALIDACION"),
        ("CERRAR", "PENDIENTE_VALIDACION", "CERRADA")]


def test_flujo_con_rechazo_y_nueva_solucion(env):
    """INT-02: rechazo conserva tecnico y solucion; nueva solucion; cierre."""
    inc = register(env)
    coord, tec, sol = env.login("coord1"), env.login("tec2"), env.login("sol1")
    coord.post(f"/incidencias/{inc}/asignar", {"tecnico_id": env.uid("tec2")})
    tec.post(f"/incidencias/{inc}/iniciar")
    tec.post(f"/incidencias/{inc}/solucion", {"solucion": "Primera solucion: se reinicio el equipo"})
    sol.post(f"/incidencias/{inc}/rechazar", {"motivo": "El dano sigue presente"})
    assert env.state(inc)["status"] == "EN_ATENCION"
    assert env.state(inc)["technician_id"] == env.uid("tec2")
    tec.post(f"/incidencias/{inc}/solucion", {"solucion": "Segunda solucion: se cambio la fuente"})
    sol.post(f"/incidencias/{inc}/confirmar")
    textos = [s["text"] for s in env.q("SELECT text FROM solutions WHERE incident_id=? ORDER BY id", (inc,))]
    assert textos == ["Primera solucion: se reinicio el equipo", "Segunda solucion: se cambio la fuente"]
    assert env.state(inc)["status"] == "CERRADA"
    assert [h[0] for h in _historial(env, inc)] == [
        "CREAR", "ASIGNAR", "INICIAR", "REGISTRAR_SOLUCION", "RECHAZAR", "REGISTRAR_SOLUCION", "CERRAR"]


def test_cierre_reapertura_nueva_solucion_y_nuevo_cierre(env):
    """INT-03: se conservan ambos cierres y ambas soluciones; reapertura con el mismo tecnico."""
    inc = register(env)
    coord, tec, sol = env.login("coord1"), env.login("tec1"), env.login("sol1")
    coord.post(f"/incidencias/{inc}/asignar", {"tecnico_id": env.uid("tec1")})
    tec.post(f"/incidencias/{inc}/iniciar")
    tec.post(f"/incidencias/{inc}/solucion", {"solucion": "Solucion inicial: se ajusto el soporte"})
    sol.post(f"/incidencias/{inc}/confirmar")
    primer_cierre = env.now
    env.now = primer_cierre + hours(30)
    assert sol.post(f"/incidencias/{inc}/reabrir", {"motivo": "La mesa volvio a cojear"}).status_code == 302
    assert env.state(inc)["technician_id"] == env.uid("tec1")
    tec.post(f"/incidencias/{inc}/solucion", {"solucion": "Nueva solucion: se cambio la pata completa"})
    env.now = env.now + hours(1)
    sol.post(f"/incidencias/{inc}/confirmar")
    cierres = [c["closed_at"] for c in env.q("SELECT closed_at FROM closures WHERE incident_id=? ORDER BY id", (inc,))]
    assert cierres == ["2026-01-05T10:00:00+00:00", "2026-01-06T17:00:00+00:00"]
    assert len(env.q("SELECT * FROM solutions WHERE incident_id=?", (inc,))) == 2
    assert env.state(inc)["last_closed_at"] == "2026-01-06T17:00:00+00:00"
    assert env.state(inc)["status"] == "CERRADA"
