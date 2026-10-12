# SPEC S02 — Priorizar y asignar

- **Versión / autor / revisor / fecha:** v0.1 / [AUTOR] / [REVISOR] / [FECHA]
- **Requisito asociado:** RF02
- **Historia:** Como **coordinador**, quiero que cada incidencia tenga prioridad calculada y asignarla a un técnico activo, para que se atienda primero lo más urgente.

## Alcance y exclusiones
Cálculo de prioridad y asignación inicial. Sin restricción de especialidad del técnico. Excluye reasignación.

## Entradas
`tecnico_id` (entero, id de un usuario con rol TECNICO y `active = 1`). La prioridad **no** es una entrada.

## Precondiciones y permisos
Rol COORDINADOR. Incidencia en REGISTRADA.

## Reglas y proceso
- Prioridad: riesgo = true → **CRITICA**; riesgo = false e impacto ALTO → **ALTA**; riesgo = false e impacto BAJO → **NORMAL**. Se calcula en el servidor al registrar.
- Asignar: en una transacción, comprobar rol, existencia, estado REGISTRADA y técnico válido/activo; pasar a ASIGNADA con `technician_id` y registrar evento ASIGNAR.

## Salidas y cambios persistidos
Incidencia ASIGNADA con técnico + evento ASIGNAR (autor = coordinador).

## Errores y efectos que deben evitarse
Rol distinto → 403. Incidencia inexistente → 404. Estado distinto de REGISTRADA (incluye reasignar) → 409. Técnico inexistente/inactivo/no técnico/no numérico → 400. Ninguno modifica estado ni historial.

## Criterios de aceptación
- **AC-S02-01** Dado un registro, cuando (riesgo, impacto) es (true, ALTO), (true, BAJO), (false, ALTO), (false, BAJO), entonces la prioridad es CRITICA, CRITICA, ALTA, NORMAL respectivamente.
- **AC-S02-02** Dado un coordinador y una incidencia REGISTRADA, cuando asigna a un técnico activo, entonces pasa a ASIGNADA con ese técnico y se registra ASIGNAR.
- **AC-S02-03** Dado un solicitante o un técnico, cuando intenta asignar, entonces recibe 403 sin cambios.
- **AC-S02-04** Dada una incidencia ya ASIGNADA, cuando el coordinador intenta asignarla de nuevo (a otro técnico o al mismo), entonces recibe 409 y se conserva el técnico original y el historial.
- **AC-S02-05** Dado un técnico inactivo, un usuario que no es técnico, un id inexistente o no numérico, cuando se intenta asignar, entonces recibe 400 sin cambios.
- **AC-S02-06** Dado un formulario con un campo `prioridad` manipulado, cuando se registra, entonces el servidor lo ignora y calcula la prioridad.

## Diseño y tareas vinculadas
| Tarea | AC | Artefacto |
|---|---|---|
| T05 `compute_priority` | 01, 06 | `services.py` |
| T06 `assign` transaccional con validación de técnico | 02–05 | `services.py` |
| T07 Ruta `POST /incidencias/<id>/asignar` y selector de técnicos activos | 02, 03 | `routes.py`, `detail.html` |

## Pruebas y resultados esperados
`tests/test_s02_priorizar_asignar.py` (6 pruebas).

## Decisión de revisión / versión aprobada
[PENDIENTE]
