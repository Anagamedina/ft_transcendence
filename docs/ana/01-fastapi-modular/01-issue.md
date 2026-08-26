# Issue 01 — FastAPI y arquitectura modular

## 1. Objetivo

Crear la base ejecutable del backend y establecer una arquitectura que separe HTTP, lógica de negocio y persistencia. El resultado debe permitir registrar módulos sin convertir `main.py` en un archivo monolítico.

## 2. Problema que resuelve

Sin una composición clara, los routers acumulan validación, consultas, reglas y manejo de errores. Esto dificulta probar cada parte y hace que añadir un nuevo módulo rompa otros.

## 3. Flujo y responsabilidades

```text
request → router → service → repository → respuesta
```

El router traduce HTTP, el service coordina negocio, el repository accede a datos y las dependencias comunes proporcionan contexto. En esta issue no se implementa SQLAlchemy.

## 4. Dependencias y límites

Puede comenzar sin dependencias. No incluye PostgreSQL, SQLAlchemy, Alembic, modelos ni reglas de dominio.

## 5. Aprendizaje estimado

FastAPI/app lifecycle — 45 min; routers/dependencies — 45 min; arquitectura por capas — 60 min; errores y pruebas de arranque — 45–60 min.

## 6. Finalidad

Es el punto de entrada estable para todas las issues posteriores. Debe arrancar, exponer `/api/health`, registrar routers modularmente y no contener acceso a datos dentro de routers.

## 7. Criterios de aceptación

- [ ] FastAPI arranca con un comando reproducible.
- [ ] `main.py` compone la aplicación y registra routers.
- [ ] Existe estructura `modules/` y separación router/service/repository.
- [ ] `/api/health` responde correctamente.
- [ ] Existe manejo global coherente de errores.
