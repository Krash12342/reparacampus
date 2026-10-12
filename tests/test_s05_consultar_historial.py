"""S05 Consultar e historizar (RF05)."""
import sqlite3

from .helpers import assign, close, hours, register, to_pending


def _codes(res):
    import re
    return re.findall(r"INC-\d{4}", res.get_data(as_text=True))


def test_listado_segun_permisos(env):
    """AC-S05-01: solicitante solo propias; tecnico solo asignadas; coordinador todas."""
    a = register(env, user="sol1")
    b = register(env, user="sol2")
    assign(env, a, "tec1")
    assert sorted(set(_codes(env.login("sol1").get("/incidencias")))) == ["INC-0001"]
    assert sorted(set(_codes(env.login("sol2").get("/incidencias")))) == ["INC-0002"]
    assert sorted(set(_codes(env.login("tec1").get("/incidencias")))) == ["INC-0001"]
    assert _codes(env.login("tec2").get("/incidencias")) == []
    assert sorted(set(_codes(env.login("coord1").get("/incidencias")))) == ["INC-0001", "INC-0002"]


def test_filtros_por_estado_y_prioridad(env):
    """AC-S05-02: filtros correctos; valores invalidos -> 400."""
    register(env, riesgo="true")                       # INC-0001 CRITICA REGISTRADA
    register(env, impacto="ALTO")                      # INC-0002 ALTA REGISTRADA
    c = register(env)                                  # INC-0003 NORMAL
    assign(env, c)                                     # ASIGNADA
    coord = env.login("coord1")
    assert set(_codes(coord.get("/incidencias?prioridad=CRITICA"))) == {"INC-0001"}
    assert set(_codes(coord.get("/incidencias?estado=ASIGNADA"))) == {"INC-0003"}
    assert set(_codes(coord.get("/incidencias?estado=REGISTRADA&prioridad=ALTA"))) == {"INC-0002"}
    assert coord.get("/incidencias?estado=INVENTADO").status_code == 400
    assert coord.get("/incidencias?prioridad=URGENTE").status_code == 400


def test_detalle_de_incidencia_ajena_o_inexistente(env):
    """AC-S05-05: otro solicitante/tecnico no asignado -> 403; inexistente -> 404."""
    inc = register(env, user="sol1")
    assert env.login("sol2").get(f"/incidencias/{inc}").status_code == 403
    assert env.login("tec1").get(f"/incidencias/{inc}").status_code == 403
    assert env.login("coord1").get(f"/incidencias/{inc}").status_code == 200
    assert env.login("sol1").get("/incidencias/9999").status_code == 404


def test_historial_no_se_edita_ni_borra(env):
    """AC-S05-04: la base rechaza UPDATE/DELETE sobre eventos, soluciones y cierres."""
    inc = register(env)
    to_pending(env, inc); close(env, inc)
    conn = sqlite3.connect(env.db_path)
    for sql in ("UPDATE events SET detail='x'", "DELETE FROM events",
                "UPDATE solutions SET text='x'", "DELETE FROM solutions",
                "UPDATE closures SET closed_at='x'", "DELETE FROM closures"):
        try:
            conn.execute(sql)
            assert False, f"debio fallar: {sql}"
        except sqlite3.DatabaseError:
            pass
    conn.close()
    assert env.n_events(inc) == 5  # CREAR, ASIGNAR, INICIAR, REGISTRAR_SOLUCION, CERRAR


def test_tablero_solo_coordinador_con_conteos_y_criticas(env):
    """AC-S05-06: conteos por estado y prioridad; CRITICA no cerradas; acceso restringido."""
    a = register(env, riesgo="true")
    register(env, impacto="ALTO")
    register(env)
    assign(env, a)
    for user in ("sol1", "tec1"):
        assert env.login(user).get("/tablero").status_code == 403
    page = env.login("coord1").get("/tablero").get_data(as_text=True)
    assert "INC-0001" in page and "INC-0002" not in page.split("CRITICA no cerradas")[1]
    assert "<td>ASIGNADA</td><td>1</td>" in page and "<td>REGISTRADA</td><td>2</td>" in page
    assert "<td>CRITICA</td><td>1</td>" in page and "<td>ALTA</td><td>1</td>" in page
    assert "<td>NORMAL</td><td>1</td>" in page


def test_porcentaje_de_cierre(env):
    """AC-S05-07: vacio=0,0 %; 1 de 4=25,0 %; reabrir reduce y conserva el cierre anterior."""
    coord = env.login("coord1")
    assert 'id="pct">0,0 %<' in coord.get("/tablero").get_data(as_text=True)
    ids = [register(env) for _ in range(4)]
    to_pending(env, ids[0]); close(env, ids[0])
    assert 'id="pct">25,0 %<' in coord.get("/tablero").get_data(as_text=True)
    env.now = env.now + hours(1)
    env.login("sol1").post(f"/incidencias/{ids[0]}/reabrir", {"motivo": "La falla volvio a aparecer"})
    assert 'id="pct">0,0 %<' in coord.get("/tablero").get_data(as_text=True)
    assert len(env.q("SELECT * FROM closures WHERE incident_id=?", (ids[0],))) == 1
    # redondeo a un decimal: 1/3 = 33,3 % ; 2/3 = 66,7 %
    for i in (1, 2):
        to_pending(env, ids[i], "tec2"); close(env, ids[i])
    page = coord.get("/tablero").get_data(as_text=True)
    assert 'id="pct">50,0 %<' in page  # 2 cerradas de 4


def test_persistencia_tras_reinicio(env):
    """AC-S05-08: los datos y el historial sobreviven a reiniciar la aplicacion."""
    inc = register(env)
    assign(env, inc)
    env.restart()
    assert env.state(inc)["status"] == "ASIGNADA"
    page = env.login("coord1").get(f"/incidencias/{inc}").get_data(as_text=True)
    assert "ASIGNAR" in page and "INC-0001" in page


def test_login_logout_y_hash_de_contrasenas(env):
    """AC-S05-03: cuentas ficticias entran; clave incorrecta no; en BD solo hay hash."""
    hashes = [r["password_hash"] for r in env.q("SELECT password_hash FROM users")]
    assert len(hashes) == 5
    assert all("Clave-2026" not in h and h.startswith(("scrypt:", "pbkdf2:")) for h in hashes)
    anon = env.login("sol1")
    assert anon.get("/incidencias").status_code == 200
    anon.post("/logout")
    assert anon.get("/incidencias").status_code == 302
    from .conftest import Browser
    bad = Browser(env)
    assert bad.login("sol1", "clave-equivocada").status_code == 401
    assert bad.get("/incidencias").status_code == 302
