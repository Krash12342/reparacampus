"""Fixtures: app sobre una base SQLite real e independiente por prueba y reloj controlado."""
import sqlite3
from datetime import datetime, timezone

import pytest

from app import create_app

PASSWORDS = {
    "sol1": "Sol1-Clave-2026", "sol2": "Sol2-Clave-2026", "coord1": "Coord1-Clave-2026",
    "tec1": "Tec1-Clave-2026", "tec2": "Tec2-Clave-2026",
}
T0 = datetime(2026, 1, 5, 10, 0, 0, tzinfo=timezone.utc)


class Browser:
    """Cliente de pruebas con sesion propia; agrega el token CSRF como lo haria el formulario."""

    def __init__(self, env):
        self.env = env
        self.client = env.app.test_client()

    def login(self, username, password=None):
        self.client.get("/login")
        return self.post("/login", {"usuario": username,
                                    "clave": password or PASSWORDS[username]})

    def get(self, url):
        return self.client.get(url)

    def post(self, url, data=None, csrf=True):
        data = dict(data or {})
        if csrf:
            with self.client.session_transaction() as sess:
                token = sess.get("csrf")
            if token is None:
                self.client.get("/login")
                with self.client.session_transaction() as sess:
                    token = sess["csrf"]
            data["csrf_token"] = token
        return self.client.post(url, data=data)


class Env:
    def __init__(self, tmp_path):
        self.db_path = str(tmp_path / "prueba.db")
        self.now = T0
        self.app = self._make_app()

    def _make_app(self):
        return create_app({"DATABASE": self.db_path, "TESTING": True,
                           "SECRET_KEY": "clave-de-pruebas", "CLOCK": lambda: self.now})

    def restart(self):
        """Simula reiniciar el servidor: nueva app sobre el mismo archivo de base de datos."""
        self.app = self._make_app()

    def login(self, username):
        browser = Browser(self)
        res = browser.login(username)
        assert res.status_code == 302, f"login de {username} fallo: {res.status_code}"
        return browser

    def q(self, sql, args=()):
        """Consulta independiente (conexion propia) para comprobar efectos en la base."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            return conn.execute(sql, args).fetchall()
        finally:
            conn.close()

    def uid(self, username):
        return self.q("SELECT id FROM users WHERE username = ?", (username,))[0]["id"]

    def state(self, inc_id):
        return self.q("SELECT * FROM incidents WHERE id = ?", (inc_id,))[0]

    def n_events(self, inc_id):
        return self.q("SELECT COUNT(*) n FROM events WHERE incident_id = ?", (inc_id,))[0]["n"]


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)
