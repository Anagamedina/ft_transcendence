# Implementación — Issue 05

## Fase 1 — Diseñar el escenario

1. Confirmar campos obligatorios y relaciones.
2. Elegir nombres/códigos demo estables y documentar qué representa cada registro.
3. Confirmar si el usuario necesita password hasheada por el flujo de Ana.

## Fase 2 — Implementar

1. Crear `backend/seeds/seed_demo.py` usando la misma configuración de DB.
2. Abrir una transacción y obtener/reutilizar registros existentes.
3. Insertar en orden organización → usuarios/sites → sensores.
4. Hacer `flush()` cuando se necesiten IDs y commit solo al final.
5. No imprimir credenciales ni usar datos de producción.

## Fase 3 — Verificar

1. Ejecutar tras `alembic upgrade head` sobre una base vacía.
2. Verificar conteos, relaciones y datos utilizables por simulador/frontend.
3. Ejecutar dos veces y comparar el resultado.
4. Romper una FK intencionadamente y confirmar rollback completo.

## Errores frecuentes

- Ejecutar seed antes de migrar.
- Crear hijos antes que padres.
- Generar IDs aleatorios en cada ejecución y duplicar datos.
- Incluir passwords en claro o datos reales.
- Hacer commit después de cada fila y dejar un seed parcial.
