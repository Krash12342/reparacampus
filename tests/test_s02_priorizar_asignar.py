"""S02 Priorizar y asignar (RF02)."""
from .helpers import assign, form, register


def test_prioridad_se_calcula_en_el_servidor(env):
    """AC-S02-01: riesgo->CRITICA; sin riesgo ALTO->ALTA; sin riesgo BAJO->NORMAL."""
    esperados = [("true", "ALTO", "CRITICA"), ("true", "BAJO", "CRITICA"),
                 ("false", "ALTO", "ALTA"), ("false", "BAJO", "NORMAL")]
    for riesgo, impacto, esperado in esperados:
        inc = register(env, riesgo=riesgo, impacto=impacto)
        assert env.state(inc)["priority"] == esperado, (riesgo, impacto)


def test_prioridad_enviada_por_el_cliente_se_ignora(env):
    """AC-S02-06: un campo prioridad en el formulario no cambia el calculo."""
    inc = register(env, riesgo="false", impacto="BAJO", prioridad="CRITICA")
    assert env.state(inc)["priority"] == "NORMAL"


def test_coordinador_asigna_registrada_a_tecnico_activo(env):
    """AC-S02-02: REGISTRADA -> ASIGNADA con tecnico y evento ASIGNAR."""
    inc = register(env)
    assign(env, inc, "tec2")
    row = env.state(inc)
    assert row["status"] == "ASIGNADA" and row["technician_id"] == env.uid("tec2")
    ev = env.q("SELECT * FROM events WHERE incident_id = ? ORDER BY id", (inc,))
    assert [e["action"] for e in ev] == ["CREAR", "ASIGNAR"]
    assert ev[1]["actor_id"] == env.uid("coord1")
    assert ev[1]["from_status"] == "REGISTRADA" and ev[1]["to_status"] == "ASIGNADA"


def test_solo_coordinador_asigna(env):
    """AC-S02-03: solicitante y tecnico -> 403 sin cambios."""
    inc = register(env)
    for user in ("sol1", "tec1"):
        res = env.login(user).post(f"/incidencias/{inc}/asignar", {"tecnico_id": env.uid("tec1")})
        assert res.status_code == 403
    assert env.state(inc)["status"] == "REGISTRADA" and env.n_events(inc) == 1


def test_asignacion_repetida_o_reasignacion_rechazada(env):
    """AC-S02-04: ya ASIGNADA no se reasigna; conserva tecnico e historial."""
    inc = register(env)
    assign(env, inc, "tec1")
    antes = env.n_events(inc)
    res = env.login("coord1").post(f"/incidencias/{inc}/asignar", {"tecnico_id": env.uid("tec2")})
    assert res.status_code == 409
    assert env.state(inc)["technician_id"] == env.uid("tec1")
    assert env.n_events(inc) == antes


def test_tecnico_inactivo_inexistente_o_no_tecnico_rechazado(env):
    """AC-S02-05: 400 y sin cambios."""
    inc = register(env)
    import sqlite3
    conn = sqlite3.connect(env.db_path)
    conn.execute("UPDATE users SET active = 0 WHERE username = 'tec2'")
    conn.commit(); conn.close()
    coord = env.login("coord1")
    for tecnico_id in (env.uid("tec2"), env.uid("sol1"), 9999, "abc", ""):
        res = coord.post(f"/incidencias/{inc}/asignar", {"tecnico_id": tecnico_id})
        assert res.status_code == 400, tecnico_id
    assert env.state(inc)["status"] == "REGISTRADA" and env.n_events(inc) == 1
