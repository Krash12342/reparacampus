# SPEC S04 — Validar solución, rechazar y reabrir

- **Versión / autor / revisor / fecha:** v0.1 / [AUTOR] / [REVISOR] / [FECHA]
- **Requisito asociado:** RF04
- **Historia:** Como **solicitante dueño**, quiero confirmar, rechazar o reabrir la solución de mi incidencia, para asegurarme de que el problema quedó resuelto de verdad.

## Alcance y exclusiones
Confirmar (→CERRADA), rechazar (→EN_ATENCION) y reabrir (CERRADA→EN_ATENCION, ≤ 48 h). Sin cierre automático; el coordinador no actúa en nombre del solicitante.

## Entradas
`motivo` (rechazo/reapertura): 10 a 300 caracteres tras strip.

## Precondiciones y permisos
Rol SOLICITANTE **y** ser el autor de la incidencia.

## Reglas y proceso
- Confirmar: estado PENDIENTE_VALIDACION → CERRADA; insertar fila en `closures` y fijar `last_closed_at` = hora del servidor (UTC).
- Rechazar: PENDIENTE_VALIDACION → EN_ATENCION, mismo técnico, soluciones conservadas; evento RECHAZAR con el motivo.
- Reabrir: estado CERRADA y `ahora − last_closed_at ≤ 48 h` (el reloj es del servidor; el navegador no envía hora) → EN_ATENCION con el mismo técnico; evento REABRIR con el motivo. Cierres y soluciones anteriores se conservan.

## Salidas y cambios persistidos
Estado, evento y, al confirmar, un cierre nuevo. Nada se borra ni se sobrescribe.

## Errores y efectos que deben evitarse
No dueño o coordinador/técnico → 403. Estado incorrecto o plazo vencido → 409. Motivo fuera de rango → 400. Operación rechazada: estado e historial intactos.

## Criterios de aceptación
- **AC-S04-01** Dado el dueño y una incidencia PENDIENTE_VALIDACION, cuando confirma, entonces queda CERRADA, con un cierre y `last_closed_at` registrados.
- **AC-S04-02** Dado otro solicitante, el coordinador o un técnico, cuando intenta confirmar, entonces recibe 403 sin cambios.
- **AC-S04-03** Dado el dueño y una incidencia PENDIENTE_VALIDACION con técnico T y solución registrada, cuando la rechaza con «El daño sigue presente», entonces queda EN_ATENCION, conserva T y la solución anterior, y registra quién rechazó, cuándo y por qué.
- **AC-S04-04** Dado un motivo de 9 caracteres (o 301, o vacío), cuando se rechaza, entonces recibe 400 y el estado y el historial no cambian; con 10 se acepta.
- **AC-S04-05** Dada una incidencia CERRADA exactamente 48 h antes, cuando el dueño la reabre con motivo válido, entonces queda EN_ATENCION con el mismo técnico.
- **AC-S04-06** Dada una incidencia CERRADA hace 48 h y 1 s, cuando el dueño intenta reabrirla, entonces recibe 409 y no cambia nada.
- **AC-S04-07** Dado otro solicitante o el coordinador intentando reabrir → 403; una incidencia no cerrada → 409; motivo corto → 400; sin cambios.
- **AC-S04-08** Dada una incidencia cerrada, reabierta, re-solucionada y cerrada de nuevo, entonces existen dos cierres y dos soluciones, ambos conservados.

## Diseño y tareas vinculadas
| Tarea | AC | Artefacto |
|---|---|---|
| T11 `confirm`, `reject`, `reopen` | 01–08 | `services.py` |
| T12 Reloj inyectable (`CLOCK`) para probar 48 h | 05, 06 | `create_app` |
| T13 Tablas `closures`/`solutions` inmutables (triggers) | 08 | `schema.sql` |

## Pruebas y resultados esperados
`tests/test_s04_validar.py` (7) + `tests/test_integracion.py` (INT-02, INT-03).

## Decisión de revisión / versión aprobada
[PENDIENTE]
