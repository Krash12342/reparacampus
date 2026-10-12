"""S04 Validar (RF04). La reapertura usa reloj controlado: no se esperan 48 h reales."""
from .helpers import close, hours, register, to_pending


def _pendiente(env):
    inc = register(env)
    to_pending(env, inc)
    return inc


def test_solicitante_duenio_confirma_y_cierra(env):
    """AC-S04-01: PENDIENTE_VALIDACION -> CERRADA; registra cierre y evento."""
    inc = _pendiente(env)
    env.now = env.now + hours(2)
    close(env, inc)
    row = env.state(inc)
    assert row["status"] == "CERRADA" and row["last_closed_at"] == "2026-01-05T12:00:00+00:00"
    assert len(env.q("SELECT * FROM closures WHERE incident_id=?", (inc,))) == 1


def test_ajeno_o_coordinador_no_confirma(env):
    """AC-S04-02: otro solicitante, coordinador y tecnico -> 403 sin cambios."""
    inc = _pendiente(env)
    antes = env.n_events(inc)
    for user in ("sol2", "coord1", "tec1"):
        assert env.login(user).post(f"/incidencias/{inc}/confirmar").status_code == 403, user
    assert env.state(inc)["status"] == "PENDIENTE_VALIDACION" and env.n_events(inc) == antes


def test_rechazo_valido_conserva_tecnico_y_solucion(env):
    """AC-S04-03: vuelve a EN_ATENCION con el mismo tecnico; guarda quien/cuando/por que."""
    inc = _pendiente(env)
    res = env.login("sol1").post(f"/incidencias/{inc}/rechazar", {"motivo": "El dano sigue presente"})
    assert res.status_code == 302
    row = env.state(inc)
    assert row["status"] == "EN_ATENCION" and row["technician_id"] == env.uid("tec1")
    assert len(env.q("SELECT * FROM solutions WHERE incident_id=?", (inc,))) == 1
    ev = env.q("SELECT * FROM events WHERE incident_id=? ORDER BY id", (inc,))[-1]
    assert (ev["action"], ev["detail"], ev["actor_id"]) == ("RECHAZAR", "El dano sigue presente",
                                                            env.uid("sol1"))
    assert (ev["from_status"], ev["to_status"]) == ("PENDIENTE_VALIDACION", "EN_ATENCION")


def test_rechazo_con_motivo_invalido_no_cambia_nada(env):
    """AC-S04-04: 9 y 301 caracteres -> 400; 10 aceptado; sin efectos en los rechazados."""
    inc = _pendiente(env)
    sol = env.login("sol1")
    antes = env.n_events(inc)
    for motivo in ("", "a" * 9, "  " + "a" * 9 + "  ", "a" * 301):
        assert sol.post(f"/incidencias/{inc}/rechazar", {"motivo": motivo}).status_code == 400
    assert env.state(inc)["status"] == "PENDIENTE_VALIDACION" and env.n_events(inc) == antes
    assert sol.post(f"/incidencias/{inc}/rechazar", {"motivo": "a" * 10}).status_code == 302


def test_reapertura_a_las_48h_exactas_se_acepta(env):
    """AC-S04-05: <= 48 h desde el ultimo cierre -> EN_ATENCION con el mismo tecnico."""
    inc = _pendiente(env)
    close(env, inc)
    cierre = env.now
    env.now = cierre + hours(48)
    res = env.login("sol1").post(f"/incidencias/{inc}/reabrir", {"motivo": "La falla volvio a aparecer"})
    assert res.status_code == 302
    row = env.state(inc)
    assert row["status"] == "EN_ATENCION" and row["technician_id"] == env.uid("tec1")


def test_reapertura_pasadas_48h_se_rechaza_sin_cambios(env):
    """AC-S04-06: 48 h + 1 s -> 409; estado e historial intactos."""
    inc = _pendiente(env)
    close(env, inc)
    env.now = env.now + hours(48, seconds=1)
    antes = env.n_events(inc)
    res = env.login("sol1").post(f"/incidencias/{inc}/reabrir", {"motivo": "La falla volvio a aparecer"})
    assert res.status_code == 409
    assert env.state(inc)["status"] == "CERRADA" and env.n_events(inc) == antes


def test_reapertura_ajeno_estado_incorrecto_y_motivo_invalido(env):
    """AC-S04-07: duenio ajeno/coordinador -> 403; no cerrada -> 409; motivo corto -> 400."""
    inc = _pendiente(env)
    sol = env.login("sol1")
    assert sol.post(f"/incidencias/{inc}/reabrir", {"motivo": "No esta cerrada aun"}).status_code == 409
    close(env, inc)
    for user in ("sol2", "coord1"):
        assert env.login(user).post(f"/incidencias/{inc}/reabrir",
                                    {"motivo": "Intento no autorizado"}).status_code == 403
    assert sol.post(f"/incidencias/{inc}/reabrir", {"motivo": "corto"}).status_code == 400
    assert env.state(inc)["status"] == "CERRADA"
