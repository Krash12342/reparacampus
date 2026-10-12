# ReparaCampus — gestión de incidencias de infraestructura

Prototipo del examen *Ingeniería de Software I — SDD + IA* (Universidad Simón Bolívar).
Monolito modular: **Flask + SQLite**, plantillas Jinja, HTML/CSS/JavaScript y **pytest**.

## Versiones (registrar las exactas del equipo)
| Componente | Versión usada en el desarrollo |
|---|---|
| Python | 3.12.3 |
| Flask | 3.1.3 |
| Werkzeug | 3.1.7 |
| pytest | **[COMPLETAR: salida de `pytest --version`]** |

## Instalación y arranque desde una copia limpia
```bash
git clone <URL-DEL-REPOSITORIO> && cd reparacampus
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app run init-db        # crea instance/reparacampus.db con el esquema y el seed ficticio
flask --app run run            # http://127.0.0.1:5000
```
Variables opcionales: `REPARACAMPUS_DB` (ruta de la base), `REPARACAMPUS_SECRET_KEY` (clave de sesión; cámbiela fuera del prototipo).

## Cuentas ficticias (seed)
| Usuario | Rol | Clave |
|---|---|---|
| sol1 | SOLICITANTE | Sol1-Clave-2026 |
| sol2 | SOLICITANTE | Sol2-Clave-2026 |
| coord1 | COORDINADOR | Coord1-Clave-2026 |
| tec1 | TECNICO | Tec1-Clave-2026 |
| tec2 | TECNICO | Tec2-Clave-2026 |

En la base solo se guardan hashes (Werkzeug). Todos los datos son ficticios.

## Pruebas
```bash
pytest -v                 # 36 pruebas; cada una usa su propia base SQLite temporal
pytest -v -m integration  # 3 pruebas de integración (flujos completos)
```
Las pruebas usan un **reloj controlado** (`CLOCK` en `create_app`) para verificar el límite de 48 h sin esperar y sin tocar el reloj del sistema.

## Estructura
```
app/            routes.py (sesión, CSRF, vistas) · services.py (reglas) · db.py · schema.sql · templates/ · static/
specs/          S01 a S05 (especificación, criterios, plan y tareas)
docs/           diseño, riesgos, trazabilidad, bitácora de IA y borrador del PDF
tests/          pytest + cliente de pruebas de Flask
```

## Reglas de diseño que conviene recordar
- Toda regla de negocio y permiso se ejecuta en el servidor (`services.py`); ocultar botones no es seguridad.
- Orden de comprobación: rol/pertenencia (403) → existencia (404) → estado (409) → entradas (400).
- Estado e historial se guardan en una sola transacción (`BEGIN IMMEDIATE … COMMIT/ROLLBACK`).
- Eventos, soluciones y cierres son inmutables (triggers de SQLite).

## Limitaciones conocidas
- Sin adjuntos, notificaciones, hosting ni IA dentro del producto (fuera de alcance del caso).
- La hora se muestra en UTC.
- Mensajes de error en una página genérica (prototipo).
