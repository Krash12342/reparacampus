# SPEC S05 — Consultar e historizar

- **Versión / autor / revisor / fecha:** v0.1 / [AUTOR] / [REVISOR] / [FECHA]
- **Requisito asociado:** RF05
- **Historia:** Como **usuario del sistema**, quiero consultar las incidencias que me corresponden con filtros y ver su historial inmutable; como **coordinador**, quiero un tablero con cantidades y porcentaje de cierre, para dar seguimiento.

## Alcance y exclusiones
Listado con filtros, detalle con historial, tablero, autenticación y persistencia. Excluye exportaciones y notificaciones.

## Entradas
`estado` (uno de los 5 estados) y `prioridad` (CRITICA/ALTA/NORMAL), opcionales.

## Precondiciones y permisos
Sesión iniciada. Solicitante: solo sus incidencias. Técnico: solo las asignadas. Coordinador: todas y el tablero.

## Reglas y proceso
- Cada creación y transición exitosa inserta un evento (autor, fecha, estado origen/destino, acción, detalle) en la **misma transacción** que el cambio.
- Eventos, soluciones y cierres no se editan ni se borran (triggers de SQLite).
- Tablero: conteo por estado y por prioridad, lista de CRITICA no cerradas y porcentaje = CERRADAS / total × 100 con un decimal (redondeo half-up), formato `25,0 %`; con 0 registros `0,0 %`.
- Contraseñas con hash (scrypt/pbkdf2 de Werkzeug); identidad y rol salen de la sesión del servidor.

## Salidas y cambios persistidos
Vistas de listado, detalle y tablero. Los datos persisten en el archivo SQLite al reiniciar.

## Errores y efectos que deben evitarse
Filtro inválido → 400. Detalle ajeno → 403; inexistente → 404. Tablero para no coordinador → 403. Una operación fallida no deja eventos.

## Criterios de aceptación
- **AC-S05-01** Dadas incidencias de dos solicitantes y una asignada a tec1, cuando cada rol consulta, entonces sol1/sol2 ven solo las suyas, tec1 solo la asignada, tec2 ninguna y el coordinador todas.
- **AC-S05-02** Dados filtros por estado y/o prioridad, cuando se consulta, entonces solo aparecen las coincidentes; un valor inválido devuelve 400.
- **AC-S05-03** Dadas las 5 cuentas ficticias, cuando inician sesión, entonces entran; con clave errónea no; en la base solo hay hashes; al cerrar sesión se pierde el acceso.
- **AC-S05-04** Dada una incidencia con historial, cuando se intenta UPDATE/DELETE sobre eventos, soluciones o cierres, entonces la base lo rechaza; el flujo completo deja 5 eventos en el orden esperado.
- **AC-S05-05** Dado otro solicitante o un técnico no asignado, cuando abre el detalle, entonces recibe 403; un id inexistente devuelve 404.
- **AC-S05-06** Dado el coordinador, cuando abre el tablero, entonces ve conteos por estado y prioridad y las CRITICA no cerradas; solicitante y técnico reciben 403.
- **AC-S05-07** Dado el tablero, entonces: 0 registros → `0,0 %`; 1 cerrada de 4 → `25,0 %`; reabrir esa incidencia → `0,0 %` conservando su cierre anterior; 2 de 4 → `50,0 %`.
- **AC-S05-08** Dado un servidor reiniciado, entonces estados, soluciones, cierres e historial siguen presentes.

## Diseño y tareas vinculadas
| Tarea | AC | Artefacto |
|---|---|---|
| T14 Login/logout, hash, CSRF, carga de usuario por sesión | 03 | `routes.py` |
| T15 `list_incidents`, `get_detail` con alcance por rol | 01, 02, 05 | `services.py` |
| T16 `dashboard` y `format_percent` | 06, 07 | `services.py`, `dashboard.html` |
| T17 Triggers de inmutabilidad y seed | 04, 08 | `schema.sql`, `db.py` |

## Pruebas y resultados esperados
`tests/test_s05_consultar_historial.py` (8) + `tests/test_integracion.py` (INT-01).

## Decisión de revisión / versión aprobada
[PENDIENTE]
