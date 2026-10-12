from datetime import timedelta

DESC = "Proyector del aula sin senal de video"  # 37 caracteres


def form(**over):
    base = {"ubicacion": "LAB-01", "categoria": "TIC", "impacto": "BAJO",
            "riesgo": "false", "descripcion": DESC}
    base.update(over)
    return base


def register(env, user="sol1", **over):
    res = env.login(user).post("/incidencias/nueva", form(**over))
    assert res.status_code == 302, res.get_data(as_text=True)
    return env.q("SELECT MAX(id) m FROM incidents")[0]["m"]


def assign(env, inc_id, tech="tec1"):
    res = env.login("coord1").post(f"/incidencias/{inc_id}/asignar",
                                   {"tecnico_id": env.uid(tech)})
    assert res.status_code == 302
    return res


def start(env, inc_id, tech="tec1"):
    res = env.login(tech).post(f"/incidencias/{inc_id}/iniciar")
    assert res.status_code == 302
    return res


def solve(env, inc_id, tech="tec1", text="Se cambio el cable HDMI y se probo la senal"):
    res = env.login(tech).post(f"/incidencias/{inc_id}/solucion", {"solucion": text})
    assert res.status_code == 302
    return res


def to_pending(env, inc_id, tech="tec1"):
    assign(env, inc_id, tech)
    start(env, inc_id, tech)
    solve(env, inc_id, tech)


def close(env, inc_id, user="sol1"):
    res = env.login(user).post(f"/incidencias/{inc_id}/confirmar")
    assert res.status_code == 302
    return res


def hours(n, seconds=0):
    return timedelta(hours=n, seconds=seconds)
