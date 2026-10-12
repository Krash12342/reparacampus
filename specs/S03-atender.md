# SPEC S03 — Atender

- **Versión / autor / revisor / fecha:** v0.1 / [AUTOR] / [REVISOR] / [FECHA]
- **Requisito asociado:** RF03
- **Historia:** Como **técnico asignado**, quiero iniciar la atención y registrar la solución, para que el solicitante pueda validarla.

## Alcance y exclusiones
Transiciones ASIGNADA→EN_ATENCION y EN_ATENCION→PENDIENTE_VALIDACION. Excluye cierre y reasignación.

## Entradas
`solucion`: texto de 20 a 800 caracteres tras strip (solo al registrar solución).

## Precondiciones y permisos
Rol TECNICO **y** ser el técnico asignado a esa incidencia (se comprueba en el servidor).

## Reglas y proceso
Iniciar: estado ASIGNADA → EN_ATENCION (evento INICIAR). Registrar solución: estado EN_ATENCION; en una transacción insertar la solución (tabla `solutions`, nunca se sobrescribe), pasar a PENDIENTE_VALIDACION y registrar REGISTRAR_SOLUCION con el texto.

## Salidas y cambios persistidos
Cambio de estado + evento; nueva fila en `solutions` al registrar solución.

## Errores y efectos que deben evitarse
Otro rol o técnico no asignado → 403. Estado incorrecto (p. ej. solución en ASIGNADA) → 409. Longitud fuera de rango → 400. Sin efectos parciales.

## Criterios de aceptación
- **AC-S03-01** Dado el técnico asignado y una incidencia ASIGNADA, cuando inicia la atención, entonces pasa a EN_ATENCION y se registra INICIAR.
- **AC-S03-02** Dado otro técnico, un solicitante o el coordinador, cuando intenta iniciar, entonces recibe 403 sin cambios.
- **AC-S03-03** Dada una incidencia ASIGNADA (no iniciada), cuando el técnico registra una solución, entonces recibe 409 y no se guarda solución.
- **AC-S03-04** Dado el técnico asignado y una incidencia EN_ATENCION, cuando registra una solución válida, entonces pasa a PENDIENTE_VALIDACION, se guarda el texto y se registra el evento.
- **AC-S03-05** Dada una solución de 19 caracteres (o 801), cuando se envía, entonces se rechaza con 400; de 20 u 800 se acepta.
- **AC-S03-06** Dado un técnico no asignado, cuando intenta registrar solución, entonces recibe 403 sin cambios.

## Diseño y tareas vinculadas
| Tarea | AC | Artefacto |
|---|---|---|
| T08 `start` y `solve` transaccionales | 01, 03–05 | `services.py` |
| T09 Comprobación de pertenencia del técnico | 02, 06 | `_assigned_technician` |
| T10 Formularios en el detalle | 01, 04 | `detail.html` |

## Pruebas y resultados esperados
`tests/test_s03_atender.py` (6 pruebas).

## Decisión de revisión / versión aprobada
[PENDIENTE]
