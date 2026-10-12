"""S03 Atender (RF03)."""
from .helpers import assign, register, solve, start


def test_tecnico_asignado_inicia_atencion(env):
    """AC-S03-01: ASIGNADA -> EN_ATENCION con evento INICIAR."""
    inc = register(env)
    assign(env, inc)
    start(env, inc)
    assert env.state(inc)["status"] == "EN_ATENCION"
    assert env.q("SELECT action FROM events WHERE incident_id=? ORDER BY id", (inc,))[-1][0] == "INICIAR"


def test_no_asignado_u_otro_rol_no_inicia(env):
    """AC-S03-02: otro tecnico, solicitante y coordinador -> 403 sin cambios."""
    inc = register(env)
    assign(env, inc, "tec1")
    for user in ("tec2", "sol1", "coord1"):
        assert env.login(user).post(f"/incidencias/{inc}/iniciar").status_code == 403, user
    assert env.state(inc)["status"] == "ASIGNADA" and env.n_events(inc) == 2


def test_solucion_antes_de_iniciar_rechazada(env):
    """AC-S03-03: en ASIGNADA no se registra solucion (409)."""
    inc = register(env)
    assign(env, inc)
    res = env.login("tec1").post(f"/incidencias/{inc}/solucion",
                                 {"solucion": "Se reemplazo el cable de video del aula"})
    assert res.status_code == 409
    assert env.state(inc)["status"] == "ASIGNADA"
    assert env.q("SELECT COUNT(*) n FROM solutions")[0]["n"] == 0


def test_solucion_valida_pasa_a_pendiente_validacion(env):
    """AC-S03-04: EN_ATENCION -> PENDIENTE_VALIDACION con solucion y evento."""
    inc = register(env)
    assign(env, inc); start(env, inc)
    solve(env, inc, text="Se reemplazo el cable HDMI y se verifico la imagen")
    assert env.state(inc)["status"] == "PENDIENTE_VALIDACION"
    sol = env.q("SELECT * FROM solutions WHERE incident_id = ?", (inc,))
    assert len(sol) == 1 and sol[0]["text"] == "Se reemplazo el cable HDMI y se verifico la imagen"
    assert sol[0]["technician_id"] == env.uid("tec1")


def test_limites_de_solucion(env):
    """AC-S03-05: 19 y 801 rechazan; 20 y 800 aceptan (con strip)."""
    inc = register(env)
    assign(env, inc); start(env, inc)
    tec = env.login("tec1")
    url = f"/incidencias/{inc}/solucion"
    assert tec.post(url, {"solucion": "a" * 19}).status_code == 400
    assert tec.post(url, {"solucion": "  " + "a" * 19 + " "}).status_code == 400
    assert tec.post(url, {"solucion": "a" * 801}).status_code == 400
    assert env.state(inc)["status"] == "EN_ATENCION"
    assert tec.post(url, {"solucion": "a" * 20}).status_code == 302
    inc2 = register(env)
    assign(env, inc2); start(env, inc2)
    assert tec.post(f"/incidencias/{inc2}/solucion", {"solucion": "b" * 800}).status_code == 302


def test_tecnico_no_asignado_no_registra_solucion(env):
    """AC-S03-06: otro tecnico -> 403 sin cambios."""
    inc = register(env)
    assign(env, inc, "tec1"); start(env, inc, "tec1")
    res = env.login("tec2").post(f"/incidencias/{inc}/solucion",
                                 {"solucion": "Intento de solucion de otro tecnico"})
    assert res.status_code == 403
    assert env.q("SELECT COUNT(*) n FROM solutions")[0]["n"] == 0
