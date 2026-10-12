**Decisión:** monolito modular en Flask con SQLite, plantillas Jinja y reglas en una capa de servicios (`services.py`) separada de las rutas (`routes.py`).

| Alternativa | Ventajas | Por qué no |
|---|---|---|
| Django | Autenticación y administración incluidas | Más estructura y curva de aprendizaje de la necesaria para 5 historias y una semana |
| FastAPI + React | Separación fuerte front/back | Dos proyectos, más superficie de errores y tiempo; el caso no exige SPA |
| Reglas en el navegador | Respuesta inmediata | Incumple el requisito: el servidor debe validar permisos y reglas |

**Consecuencias:** despliegue y arranque sencillos (un proceso, un archivo de base de datos), pruebas con el cliente de Flask sobre SQLite real, y fácil de explicar. Costos: SQLite admite un solo escritor a la vez (se mitiga con transacciones cortas `BEGIN IMMEDIATE`) y una interfaz menos dinámica. La separación rutas/servicios permite cambiar la capa web sin tocar las reglas.

**Dónde se ejecuta cada cosa:** interfaz = HTML/JS (solo conveniencia); lógica y permisos = `services.py`; persistencia e inmutabilidad = SQLite (restricciones CHECK, FK y triggers).
