# Implementación — Issue 05

1. Confirmar nombres de modelos y campos obligatorios.
2. Crear `backend/seeds/seed_demo.py` usando la misma configuración de DB.
3. Insertar en orden: organización, usuarios, sites, sensores; usar datos sintéticos.
4. Hacer el script repetible mediante búsqueda por email/código o una política documentada.
5. Ejecutar tras `alembic upgrade head`; verificar conteos y FK.
6. Ejecutar dos veces y comprobar que el resultado sigue siendo válido.
