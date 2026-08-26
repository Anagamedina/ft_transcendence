# Issue 07 — Repositories de Users y Organizations

## 1. Objetivo

Dar persistencia a usuarios y organizaciones para que registro, login, perfil y aislamiento multi-organización puedan construirse sobre datos fiables. Esta issue implementa acceso a datos, no autenticación.

La pregunta central es: ¿puede el sistema encontrar y crear usuarios de forma consistente, garantizando que cada usuario pertenece a una organización y que su email no se duplica?

## 2. Flujo esperado

```text
router auth → auth service → User/Organization repository → Session → PostgreSQL
```

El service de Ana decidirá credenciales, hash, permisos y respuestas HTTP; el repository se ocupa de persistencia.

## 3. Requisitos y límites

Buscar usuario por email, crear usuario, consultar organización, mantener transacciones y garantizar email único. No incluye login, hash, registro HTTP ni permisos.

## 4. Decisiones importantes

- Normalización de email antes de comprobar unicidad.
- Constraint único en DB, además de comprobación amigable en service.
- `organization_id` obligatorio cuando el dominio lo exige.
- Error de integridad traducible sin filtrar detalles internos.
- Transacción coherente al crear usuario y asociarlo.

## 5. Dependencias y coordinación

Depende de modelos, migraciones y session. Ana depende de `get_by_email`, creación y consulta de organización para Register/Login, `/api/me` y permisos.

## 6. Aprendizaje estimado

Multi-tenancy y claves únicas — 40 min; repository y transacciones — 60 min; pruebas de concurrencia/casos límite — 60 min.

## 7. Finalidad para el proyecto

Es la base del aislamiento de datos y de la identidad del sistema. Una decisión incorrecta aquí puede permitir duplicados o cruces entre organizaciones.

## 8. Criterios de aceptación

- [ ] Se busca usuario por email normalizado.
- [ ] Se crea usuario asociado a una organización válida.
- [ ] Email único garantizado por constraint de PostgreSQL.
- [ ] La organización puede consultarse sin crear relaciones inválidas.
- [ ] Los errores de integridad producen rollback.
- [ ] No se implementan login, hash ni permisos en el repository.
