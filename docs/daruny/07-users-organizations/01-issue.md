# Issue 07 — Repositories de Users y Organizations

## Objetivo

Dar persistencia al registro, login, perfil y aislamiento multi-organización sin mezclar la lógica HTTP o de permisos con SQLAlchemy.

## Requisitos y límites

Buscar usuario por email, crear usuario, consultar organización, mantener transacciones y garantizar email único. No incluye login, hash, registro HTTP ni permisos.

## Aprendizaje estimado

Multi-tenancy y claves únicas — 40 min; repository y transacciones — 60 min; pruebas de concurrencia/casos límite — 60 min.

## Finalidad y aceptación

Ana puede implementar Register/Login, `/api/me` y permisos sobre una capa que devuelve datos consistentes y no permite emails duplicados.

