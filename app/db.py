"""Acceso a SQLite: conexion por solicitud, transacciones y seed ficticio."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = Path(__file__).with_name("schema.sql")

# Cuentas ficticias. Las contrasenas solo existen aqui para el seed; en BD solo hay hash.
SEED_USERS = [
    ("sol1", "Solicitante Uno", "SOLICITANTE", "Sol1-Clave-2026"),
    ("sol2", "Solicitante Dos", "SOLICITANTE", "Sol2-Clave-2026"),
    ("coord1", "Coordinador Uno", "COORDINADOR", "Coord1-Clave-2026"),
    ("tec1", "Tecnico Uno", "TECNICO", "Tec1-Clave-2026"),
    ("tec2", "Tecnico Dos", "TECNICO", "Tec2-Clave-2026"),
]


def connect(path):
    # isolation_level=None: las transacciones se manejan de forma explicita.
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def transaction(db):
    """BEGIN IMMEDIATE ... COMMIT; ROLLBACK ante cualquier excepcion (sin efectos parciales)."""
    db.execute("BEGIN IMMEDIATE")
    try:
        yield
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise


def init_db(path):
    """Crea el esquema y, si no hay usuarios, el seed ficticio. Idempotente."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    try:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            for username, name, role, password in SEED_USERS:
                conn.execute(
                    "INSERT INTO users (username, full_name, role, password_hash) VALUES (?,?,?,?)",
                    (username, name, role, generate_password_hash(password)),
                )
    finally:
        conn.close()
