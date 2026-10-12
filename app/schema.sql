PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('SOLICITANTE','COORDINADOR','TECNICO')),
    password_hash TEXT NOT NULL,
    active        INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);

CREATE TABLE IF NOT EXISTS incidents (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    code           TEXT NOT NULL UNIQUE,
    location       TEXT NOT NULL CHECK (location IN ('LAB-01','AULA-201','BIB-01')),
    category       TEXT NOT NULL CHECK (category IN ('ELECTRICIDAD','HIDRAULICA','MOBILIARIO','TIC')),
    description    TEXT NOT NULL,
    impact         TEXT NOT NULL CHECK (impact IN ('BAJO','ALTO')),
    risk           INTEGER NOT NULL CHECK (risk IN (0,1)),
    priority       TEXT NOT NULL CHECK (priority IN ('CRITICA','ALTA','NORMAL')),
    status         TEXT NOT NULL CHECK (status IN
                   ('REGISTRADA','ASIGNADA','EN_ATENCION','PENDIENTE_VALIDACION','CERRADA')),
    author_id      INTEGER NOT NULL REFERENCES users(id),
    technician_id  INTEGER REFERENCES users(id),
    created_at     TEXT NOT NULL,
    last_closed_at TEXT
);

CREATE TABLE IF NOT EXISTS solutions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id   INTEGER NOT NULL REFERENCES incidents(id),
    technician_id INTEGER NOT NULL REFERENCES users(id),
    text          TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS closures (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER NOT NULL REFERENCES incidents(id),
    closed_by   INTEGER NOT NULL REFERENCES users(id),
    closed_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER NOT NULL REFERENCES incidents(id),
    actor_id    INTEGER NOT NULL REFERENCES users(id),
    at          TEXT NOT NULL,
    action      TEXT NOT NULL,
    from_status TEXT,
    to_status   TEXT NOT NULL,
    detail      TEXT
);

-- El historial no se edita ni se borra (RF05)
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'el historial no se puede editar'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'el historial no se puede borrar'); END;
CREATE TRIGGER IF NOT EXISTS solutions_no_update BEFORE UPDATE ON solutions
BEGIN SELECT RAISE(ABORT, 'las soluciones no se pueden editar'); END;
CREATE TRIGGER IF NOT EXISTS solutions_no_delete BEFORE DELETE ON solutions
BEGIN SELECT RAISE(ABORT, 'las soluciones no se pueden borrar'); END;
CREATE TRIGGER IF NOT EXISTS closures_no_update BEFORE UPDATE ON closures
BEGIN SELECT RAISE(ABORT, 'los cierres no se pueden editar'); END;
CREATE TRIGGER IF NOT EXISTS closures_no_delete BEFORE DELETE ON closures
BEGIN SELECT RAISE(ABORT, 'los cierres no se pueden borrar'); END;

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_events_incident ON events(incident_id);
