# Issue 05 — Seed inicial de desarrollo

## 1. Objetivo

Crear un conjunto pequeño de datos de desarrollo que permita arrancar y demostrar AquaGuard sin insertar registros manualmente. Debe ser entendible, seguro y repetible.

La pregunta que responde esta issue es: ¿puede cualquier miembro del equipo preparar una base útil ejecutando un único comando después de las migraciones?

## 2. Flujo esperado

```text
base vacía → alembic upgrade head → seed_demo.py → datos relacionados listos
```

## 3. Requisitos y límites

Una organización, usuarios Admin/Client si aplica, 1–3 sites y sensores de ejemplo; script idempotente o con estrategia clara de limpieza. No incluye carga masiva ni analytics.

## 4. Datos mínimos y decisiones

- Una `Organization` claramente identificable.
- Un usuario Admin y un Client si el modelo/flujo lo requiere.
- Uno a tres `Site` y sensores representativos.
- Valores sintéticos, documentados y no sensibles.
- Estrategia definida ante una segunda ejecución: idempotencia o limpieza explícita.
- Una transacción para no dejar datos a medias.

## 5. Dependencias

Depende de modelos, migraciones y session. El simulador y las pruebas del vertical slice dependen de que existan sensores válidos.

## 6. Aprendizaje estimado

Fixtures y datos relacionales — 30 min; idempotencia/transacciones — 45 min; ejecución y verificación — 45–60 min.

## 7. Finalidad para el proyecto

El seed reduce el tiempo de onboarding, hace reproducibles las demos y proporciona las referencias que necesitan backend, frontend y simulador. No representa datos reales ni sustituye tests con fixtures aisladas.

## 8. Criterios de aceptación

- [ ] Funciona sobre una base vacía después de `upgrade head`.
- [ ] Crea la organización, usuarios, sites y sensores necesarios.
- [ ] Todas las FK son válidas y los datos sirven para el vertical slice.
- [ ] Repetirlo no crea duplicados inesperados.
- [ ] No contiene secretos reales ni depende de intervención manual.
- [ ] Si falla una inserción, no queda un estado parcial.
