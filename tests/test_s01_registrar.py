"""S01 Registrar (RF01). Los esperados estan escritos a mano, no calculados con el codigo."""
from .helpers import DESC, form, register


def test_registro_valido_crea_reporte_registrada(env):
    """AC-S01-01: datos validos -> REGISTRADA con codigo, autor, fecha y evento CREAR."""
    sol = env.login("sol1")
    res = sol.post("/incidencias/nueva", form())
    assert res.status_code == 302
    row = env.q("SELECT * FROM incidents")[0]
    assert row["code"] == "INC-0001"
    assert row["status"] == "REGISTRADA"
    assert row["author_id"] == env.uid("sol1")
    assert row["created_at"] == "2026-01-05T10:00:00+00:00"
    assert row["technician_id"] is None
    ev = env.q("SELECT * FROM events")
    assert len(ev) == 1 and ev[0]["action"] == "CREAR"
    assert ev[0]["from_status"] is None and ev[0]["to_status"] == "REGISTRADA"
    assert ev[0]["actor_id"] == env.uid("sol1")


def test_solo_solicitante_registra_y_sin_sesion_redirige(env):
    """AC-S01-02: coordinador/tecnico -> 403; sin sesion -> login; sin efectos."""
    for user in ("coord1", "tec1"):
        assert env.login(user).post("/incidencias/nueva", form()).status_code == 403
    anon = env.app.test_client()
    assert anon.get("/incidencias/nueva").status_code == 302
    assert env.q("SELECT COUNT(*) n FROM incidents")[0]["n"] == 0


def test_campos_obligatorios_y_valores_invalidos_rechazados(env):
    """AC-S01-03 / AC-S01-04: faltantes e invalidos -> 400 y nada se guarda."""
    sol = env.login("sol1")
    casos = [{"ubicacion": ""}, {"categoria": ""}, {"impacto": ""}, {"riesgo": ""},
             {"descripcion": ""}, {"ubicacion": "PATIO-9"}, {"categoria": "JARDIN"},
             {"impacto": "MEDIO"}, {"impacto": "alto"}, {"riesgo": "quiza"}, {"riesgo": "1"}]
    for over in casos:
        assert sol.post("/incidencias/nueva", form(**over)).status_code == 400, over
    assert env.q("SELECT COUNT(*) n FROM incidents")[0]["n"] == 0
    assert env.q("SELECT COUNT(*) n FROM events")[0]["n"] == 0


def test_limites_de_descripcion_con_strip(env):
    """AC-S01-05: 19 rechaza, 20 acepta, 500 acepta, 501 rechaza; espacios externos no cuentan."""
    sol = env.login("sol1")
    assert sol.post("/incidencias/nueva", form(descripcion="a" * 19)).status_code == 400
    assert sol.post("/incidencias/nueva", form(descripcion="  " + "a" * 19 + "  ")).status_code == 400
    assert sol.post("/incidencias/nueva", form(descripcion="a" * 20)).status_code == 302
    assert sol.post("/incidencias/nueva", form(descripcion="b" * 500)).status_code == 302
    assert sol.post("/incidencias/nueva", form(descripcion="c" * 501)).status_code == 400
    assert env.q("SELECT COUNT(*) n FROM incidents")[0]["n"] == 2


def test_texto_con_html_no_se_ejecuta(env):
    """AC-S01-06: el texto parecido a HTML se muestra escapado."""
    payload = "<script>alert('x')</script> luz"
    inc = register(env, descripcion=payload)
    page = env.login("sol1").get(f"/incidencias/{inc}").get_data(as_text=True)
    assert "<script>alert('x')</script>" not in page
    assert "&lt;script&gt;alert(" in page


def test_csrf_es_obligatorio(env):
    """AC-S01-07: un POST sin token valido se rechaza sin efectos."""
    sol = env.login("sol1")
    assert sol.post("/incidencias/nueva", form(), csrf=False).status_code == 400
    assert env.q("SELECT COUNT(*) n FROM incidents")[0]["n"] == 0
