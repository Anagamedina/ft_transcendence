# Implementación — Issue 11

## Fase 1 — Definir contratos

1. Elegir endpoint de liveness/readiness del backend.
2. Decidir si readiness comprueba solo proceso o también DB.
3. Definir cómo identificar la reading creada por el smoke test.
4. Elegir timeout total y mensajes de error.

## Fase 2 — Healthchecks

1. Añadir healthcheck PostgreSQL con `pg_isready`.
2. Añadir healthcheck backend con timeout y ruta estable.
3. Configurar `depends_on` para esperar DB saludable.
4. Evitar que un `sleep` fijo sea la única sincronización.

## Fase 3 — Smoke test

1. Esperar readiness con reintentos limitados.
2. Enviar una lectura sintética válida.
3. Comprobar status HTTP y respuesta mínima.
4. Consultar la persistencia y verificar el identificador/valor esperado.
5. Limpiar datos si el entorno lo requiere, sin borrar un volumen compartido.

## Fase 4 — Integración

1. Ejecutar con Compose desde cero.
2. Apagar DB y confirmar que el test falla con diagnóstico.
3. Usar un comando reproducible en README/Makefile/CI.
4. Confirmar código de salida distinto de cero ante cualquier fallo.

## Errores frecuentes

- Confundir `running` con `healthy`.
- Usar sleeps largos en lugar de readiness.
- Comprobar solo un `200` sin verificar persistencia.
- Usar datos fijos que chocan al repetir el test.
- Ocultar excepciones y devolver siempre éxito.
