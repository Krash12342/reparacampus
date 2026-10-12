| ID | Tipo | Riesgo | Causa | Impacto | Control | Responsable | Evidencia de verificación |
|---|---|---|---|---|---|---|---|
| R1 | IA | La IA inventa que el técnico (u otro rol) puede cerrar un reporte | El prompt no incluye la matriz de permisos y la IA «completa» con lo que parece lógico | Cierres sin validación del dueño; incumple RF04 | La SPEC S04 fija quién puede cada acción; el servidor aplica `_require_role` y `_owned` en cada operación (no es una advertencia en el prompt); se pide a la IA cambios acotados por AC | [INTEGRANTE] | Pruebas AC-S04-02, AC-S03-02; mutación M3 (quitar la comprobación de dueño) hace fallar 2 pruebas |
| R2 | IA | Una prueba generada por IA acepta el mismo error del código | La IA deriva el esperado del código que escribió (circularidad) | Falsa sensación de cumplimiento | Esperados escritos a mano desde el AC antes de ejecutar; no se usa `compute_priority` ni `format_percent` en las pruebas; mutaciones manuales del código (M1: `>=` por `>` en 48 h; M2: borrar técnico al rechazar) | [INTEGRANTE] | Cada mutación debe hacer fallar al menos una prueba (ver tabla de mutaciones) |
| R3 | Producto | Un solicitante ve o actúa sobre reportes de otros | Permisos solo en la interfaz, o filtros olvidados en una ruta | Fuga de información y acciones indebidas | Identidad y rol salen de la sesión del servidor; `can_view`/`_owned` en cada operación; listado filtrado por rol en SQL; CSRF | [INTEGRANTE] | AC-S05-01, AC-S05-05, AC-S04-02/07; prueba CSRF AC-S01-07 |
| R4 | Equipo/Producto | Historial engañoso tras una operación fallida o editado después | Escritura parcial (cambia estado pero no evento) o historial modificable | Auditoría poco confiable; reportes «cerrados sin saber si quedó resuelto» | Una transacción por operación con ROLLBACK; triggers que impiden UPDATE/DELETE en eventos, soluciones y cierres | [INTEGRANTE] | AC-S05-04, AC-S04-04/06 (conteo de eventos antes/después), INT-01 a INT-03 |

### Mutaciones realizadas durante la preparación
| ID | Cambio al código | Pruebas que fallaron |
|---|---|---|
| M1 | Plazo de reapertura `>=` en lugar de `>` (rechaza justo a las 48 h) | `test_reapertura_a_las_48h_exactas_se_acepta` |
| M2 | El rechazo borra el técnico asignado | `test_rechazo_valido_conserva_tecnico_y_solucion`, `test_flujo_con_rechazo_y_nueva_solucion` |
| M3 | Se elimina la comprobación de dueño | `test_ajeno_o_coordinador_no_confirma`, `test_reapertura_ajeno_estado_incorrecto_y_motivo_invalido` |

*Repitan estas mutaciones con `pytest` real y registren fecha, comando y SHA antes de entregar.*
