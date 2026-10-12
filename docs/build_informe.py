"""Genera docs/informe_borrador.md (borrador del PDF consolidado) desde specs/, docs/ y tests/."""
import ast, pathlib, re

root = pathlib.Path(__file__).resolve().parent.parent
read = lambda p: (root / p).read_text(encoding="utf-8")

# Catalogo de pruebas desde tests/ (ID, SPEC/AC, descripcion). Observado: se completa al ejecutar pytest.
rows, n = [], 0
for f in sorted((root / "tests").glob("test_*.py")):
    tree = ast.parse(f.read_text(encoding="utf-8"))
    for fn in [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name.startswith("test_")]:
        n += 1
        doc = (ast.get_docstring(fn) or "").replace("|", "/")
        acs = ", ".join(sorted(set(re.findall(r"AC-S\d\d-\d\d", doc)))) or doc.split(":")[0]
        rows.append(f"| T{n:02d} | {fn.name} | {acs} | {doc} | [COMPLETAR] |")
catalog = ("| ID | Prueba (pytest) | SPEC/AC | Entrada y esperado (escritos antes de ejecutar) | Observado / fecha / SHA |\n"
           "|---|---|---|---|---|\n" + "\n".join(rows))

specs = ""
for f in sorted((root / "specs").glob("S0*.md")):
    specs += re.sub(r"^#", "###", f.read_text(encoding="utf-8"), flags=re.M).replace("\n## ", "\n#### ") + "\n\n"

doc = f"""---
title: "Examen ISI SDD — ReparaCampus"
---

# 1. Portada

**Universidad Simón Bolívar — Programa de Ingeniería de Sistemas — Ingeniería de Software I**

**Examen:** Específica. Construye. Verifica. (SDD + IA) — Caso ReparaCampus

**Equipo:** [COMPLETAR nombre del equipo]

| Integrante | Código |
|---|---|
| [COMPLETAR] | [COMPLETAR] |
| [COMPLETAR] | [COMPLETAR] |
| [COMPLETAR] | [COMPLETAR] |

**Grupo:** [COMPLETAR] — **Docente:** [COMPLETAR] — **Fecha:** [COMPLETAR]

# 2. Índice

*(En Word: Referencias → Tabla de contenido → Actualizar, con títulos numerados y páginas numeradas.)*

# 3. Problema y alcance

**Necesidad.** La coordinación de mantenimiento recibe reportes de daños por varios canales, los atiende por otro y a veces los da por cerrados sin saber si quedaron resueltos. Se requiere un prototipo para registrar, priorizar, asignar y comprobar la solución de incidencias de infraestructura.

**Actores y permisos.**

| Actor | Puede | No puede |
|---|---|---|
| Solicitante | Registrar; consultar las propias; confirmar, rechazar o reabrir **sus** soluciones | Ver o actuar sobre incidencias ajenas |
| Coordinador | Consultar todas; asignar un técnico activo a una REGISTRADA; ver el tablero | Confirmar, rechazar o reabrir por el solicitante; reasignar |
| Técnico | Consultar sus asignaciones; iniciar atención; registrar solución | Actuar sobre incidencias no asignadas; cerrar |

**Requisitos.** RF01 Registrar · RF02 Priorizar y asignar · RF03 Atender · RF04 Validar · RF05 Consultar e historizar (ver enunciado del examen).

**Historias ↔ requisitos.** S01↔RF01, S02↔RF02, S03↔RF03, S04↔RF04, S05↔RF05.

**Límites del prototipo.** Ubicaciones LAB-01, AULA-201, BIB-01; categorías ELECTRICIDAD, HIDRAULICA, MOBILIARIO, TIC; sin especialidad de técnico; 2 solicitantes, 1 coordinador y 2 técnicos ficticios; sin adjuntos, notificaciones, hosting ni IA en el producto.

{read("docs/preguntas-y-supuestos.md")}

# 4. SPECS

*Antes de implementar cada SPEC, otro integrante la revisa y deja fecha, versión y decisión (campos [PENDIENTE]). Adjunten la evidencia del commit de revisión.*

{specs}
# 5. Diseño

## 5.1 Componentes
![Componentes](diagramas/componentes.png)

Interfaz (HTML/CSS/JS), capa web (`routes.py`: sesión, CSRF, vistas), lógica (`services.py`: reglas, permisos, estados) y persistencia (`db.py` + SQLite).

## 5.2 Modelo de datos
![Modelo de datos](diagramas/datos.png)

`incidents` guarda el estado actual; `solutions`, `closures` y `events` son registros históricos que nunca se editan ni se borran (triggers).

## 5.3 UML de estados
![Estados](diagramas/estados.png)

## 5.4 UML de secuencia — rechazo de solución
![Secuencia de rechazo](diagramas/secuencia_rechazo.png)

## 5.5 Decisión tecnológica

{read("docs/decision-tecnologica.md")}

# 6. Implementación con IA

**Herramientas y versiones.** Python 3.12.3 · Flask 3.1.3 · Werkzeug 3.1.7 · SQLite (módulo estándar) · pytest [COMPLETAR versión] · Git/GitHub · diagrams.net o PlantUML · asistente de IA: [COMPLETAR herramienta y modelo].

## 6.1 Bitácora de IA (cuatro intervenciones)

{read("docs/bitacora-ia-plantilla.md")}

## 6.2 Evidencia por funcionalidad

| Funcionalidad | Módulo / archivo | Pruebas | Evidencia (captura explicada / commit) |
|---|---|---|---|
| RF01 Registrar | `services.create_incident`, `new.html` | S01 | [COMPLETAR] |
| RF02 Priorizar y asignar | `compute_priority`, `assign` | S02 | [COMPLETAR] |
| RF03 Atender | `start`, `solve` | S03 | [COMPLETAR] |
| RF04 Validar | `confirm`, `reject`, `reopen` | S04 + integración | [COMPLETAR] |
| RF05 Consultar e historizar | `list_incidents`, `get_detail`, `dashboard` | S05 | [COMPLETAR] |

# 7. Validación

## 7.1 Matriz de trazabilidad

| Requisito | Historia | SPEC | Código | Prueba |
|---|---|---|---|---|
| RF01 | H01 | S01 (AC-S01-01…07) | `create_incident`, schema CHECK | `test_s01_registrar.py` |
| RF02 | H02 | S02 (AC-S02-01…06) | `compute_priority`, `assign` | `test_s02_priorizar_asignar.py` |
| RF03 | H03 | S03 (AC-S03-01…06) | `start`, `solve` | `test_s03_atender.py` |
| RF04 | H04 | S04 (AC-S04-01…08) | `confirm`, `reject`, `reopen` | `test_s04_validar.py`, `test_integracion.py` |
| RF05 | H05 | S05 (AC-S05-01…08) | `list_incidents`, `get_detail`, `dashboard`, triggers | `test_s05_consultar_historial.py` |

## 7.2 Catálogo de pruebas automatizadas ({n} pruebas, 3 de integración)

Comando: `pytest -v` — Fecha: [COMPLETAR] — SHA: [COMPLETAR] — Resultado: [PEGAR resumen de pytest].

{catalog}

## 7.3 Comparación SPEC vs código

Para cada AC, completar: comportamiento esperado · archivo/módulo/commit · prueba y datos · resultado observado y efectos en la base · **Cumple / Parcial / No cumple** · diferencia detectada · corrección/regresión/evidencia final. *Si algo no se ejecutó o quedó incompleto, declárenlo como pendiente.*

**Hallazgo documentado durante el desarrollo:** la prueba AC-S01-07 (CSRF obligatorio) detectó que, tras iniciar sesión, el token de la sesión quedaba vacío y la comparación `"" == ""` aceptaba un POST sin token. Corrección: un token ausente nunca es válido y se genera un token nuevo al iniciar sesión. Regresión: 36 pruebas pasan. *(Verifiquen y registren con pytest real.)*

# 8. Riesgos

{read("docs/riesgos.md")}

# 9. Entrega reproducible

- **Repositorio:** [COMPLETAR URL] — **Tag:** `release-examen` — **SHA exacto:** [COMPLETAR]
- Instalación, arranque, seed, cuentas ficticias y comandos de pruebas: ver el README del repositorio (resumen abajo).

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flask --app run init-db
flask --app run run
pytest -v
```

**Limitaciones conocidas:** hora en UTC; mensajes de error genéricos; sin adjuntos ni notificaciones.

# 10. Contribuciones y cierre

| Integrante | Tareas | Artefactos / commits | Revisión realizada | Resultado |
|---|---|---|---|---|
| [COMPLETAR] | | | | |

**Conclusión de cumplimiento:** [COMPLETAR: qué cumple, qué queda pendiente]. **Aceptación del equipo:** [COMPLETAR].

# 11. Referencias

Flask — https://flask.palletsprojects.com · SQLite — https://www.sqlite.org/docs.html · pytest — https://docs.pytest.org · GitHub Issues — https://docs.github.com/issues · Enunciado del examen (sitio indicado por el docente).
"""
(root / "docs" / "informe_borrador.md").write_text(doc, encoding="utf-8")
print("ok", n, "pruebas")
