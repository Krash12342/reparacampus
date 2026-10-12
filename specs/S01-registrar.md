# SPEC S01 — Registrar incidencia

- **Versión / autor / revisor / fecha:** v0.1 / [AUTOR] / [REVISOR] / [FECHA]  ← *completar: la revisión por otro integrante debe ocurrir antes del código*
- **Requisito asociado:** RF01
- **Historia:** Como **solicitante**, quiero registrar una incidencia con ubicación, categoría, descripción, impacto y riesgo, para que mantenimiento pueda priorizarla y atenderla.

## Alcance y exclusiones
Incluye registro, generación de código/autor/fecha/estado y evento de creación. Excluye edición de reportes, adjuntos y notificaciones.

## Entradas
| Campo | Tipo | Obligatorio | Valores / límites |
|---|---|---|---|
| ubicacion | texto | sí | LAB-01, AULA-201, BIB-01 |
| categoria | texto | sí | ELECTRICIDAD, HIDRAULICA, MOBILIARIO, TIC |
| impacto | texto | sí | BAJO, ALTO (exacto, en mayúsculas) |
| riesgo | booleano | sí | `true` o `false` |
| descripcion | texto | sí | 20 a 500 caracteres **después de retirar espacios externos** |

## Precondiciones y permisos
Sesión iniciada con rol SOLICITANTE. Coordinador y técnico no registran (403). Sin sesión → redirección a login.

## Reglas y proceso
1. Validar CSRF y rol. 2. Normalizar texto (strip). 3. Validar valores permitidos y longitud. 4. Calcular prioridad (ver S02). 5. En **una transacción**: insertar incidencia (código `INC-NNNN`, autor = usuario de la sesión, fecha = reloj del servidor UTC, estado REGISTRADA) e insertar evento CREAR.

## Salidas y cambios persistidos
Incidencia REGISTRADA + evento CREAR (autor, fecha, estado inicial/final, acción). Respuesta 302 al detalle.

## Errores y efectos que deben evitarse
Dato faltante o inválido → 400 sin escribir nada. Texto con HTML se muestra escapado (nunca se ejecuta). El cliente no elige autor, fecha, estado ni prioridad.

## Criterios de aceptación
- **AC-S01-01** Dado un solicitante autenticado, cuando envía datos válidos, entonces se crea la incidencia INC-0001 en REGISTRADA con su autor, fecha UTC del servidor y un evento CREAR.
- **AC-S01-02** Dado un coordinador, un técnico o un visitante sin sesión, cuando intenta registrar, entonces recibe 403 (o redirección a login) y no se crea nada.
- **AC-S01-03** Dado un solicitante, cuando omite cualquier campo obligatorio, entonces recibe 400 y no hay incidencia ni evento nuevos.
- **AC-S01-04** Dado un solicitante, cuando envía ubicación, categoría, impacto o riesgo fuera de los valores permitidos (p. ej. impacto `MEDIO`, riesgo `quiza`), entonces recibe 400 sin efectos.
- **AC-S01-05** Dado un solicitante, cuando la descripción tiene 19 caracteres (también 19 + espacios externos) o 501, entonces se rechaza; con 20 o 500 se acepta.
- **AC-S01-06** Dada una descripción `<script>alert('x')</script> luz`, cuando se consulta el detalle, entonces el texto aparece escapado y no se ejecuta.
- **AC-S01-07** Dado un POST sin token CSRF válido, cuando se envía, entonces recibe 400 sin efectos.

## Diseño y tareas vinculadas
| Tarea | AC | Artefacto |
|---|---|---|
| T01 Esquema `incidents`/`events` con CHECK de valores permitidos | 01, 04 | `app/schema.sql` |
| T02 `create_incident` transaccional | 01, 03, 05 | `app/services.py` |
| T03 Ruta y formulario `/incidencias/nueva` | 01, 02, 07 | `routes.py`, `new.html` |
| T04 Escape de salida (autoescape Jinja) | 06 | `templates/` |

## Pruebas y resultados esperados
`tests/test_s01_registrar.py` (6 pruebas). Esperado: todas pasan; tras un rechazo, `COUNT(incidents)` y `COUNT(events)` no cambian.

## Decisión de revisión / versión aprobada
[PENDIENTE: Aprobada / Con cambios — revisor, fecha, versión]
