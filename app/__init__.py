"""ReparaCampus: gestion de incidencias de infraestructura (monolito modular Flask + SQLite)."""
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask

from . import db as database


def utc_now():
    return datetime.now(timezone.utc)


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.environ.get("REPARACAMPUS_SECRET_KEY", "dev-solo-para-el-prototipo-cambiar"),
        DATABASE=os.environ.get("REPARACAMPUS_DB",
                                str(Path(app.instance_path) / "reparacampus.db")),
        CLOCK=utc_now,  # el servidor decide la hora; las pruebas inyectan un reloj controlado
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)

    database.init_db(app.config["DATABASE"])
    app.teardown_appcontext(database.close_db)

    from .routes import bp
    app.register_blueprint(bp)

    @app.cli.command("init-db")
    def init_db_command():
        database.init_db(app.config["DATABASE"])
        print("Base de datos lista:", app.config["DATABASE"])

    return app
