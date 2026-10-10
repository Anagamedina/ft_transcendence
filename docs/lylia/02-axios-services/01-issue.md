# Issue 02 — Axios, Services y manejo común de API

## 1. Objetivo

Crear una única frontera de comunicación entre Vue y FastAPI, con baseURL, errores y autenticación configurables, evitando HTTP directo en componentes.

## 2. Problema que resuelve

Requests dispersas generan URLs distintas, errores incompatibles y lógica duplicada. Un adapter/service central facilita cambiar backend, mock o entorno.

## 3. Requisitos y límites

Configurar Axios o equivalente, `services/`, baseURL, errores e interceptores si son necesarios. No incluye diseño visual ni implementación de vistas.

## 4. Dependencias

Depende de setup Vue y de contratos OpenAPI/backend. Debe alinearse con Auth Store y MockAdapter; Florinda no debe importar Axios.

## 5. Aprendizaje estimado

HTTP/REST — 30 min; Axios — 30 min; adapters — 45 min; interceptores/auth — 45 min; errores/reintentos — 45 min; tests — 60 min.

## 6. Finalidad

Todo acceso a API pasa por una interfaz estable y los componentes quedan centrados en presentación.

## 7. Criterios de aceptación

- [ ] BaseURL configurable por entorno.
- [ ] Services organizados por dominio.
- [ ] Componentes no usan Axios directamente.
- [ ] Error común normalizado.
- [ ] Auth headers/cookies respetan la estrategia elegida.
- [ ] MockAdapter puede sustituir HttpAdapter.

## 7. Casos límite

Timeout, backend caído, 401, 403, 404, 422, 500, respuesta inesperada y token expirado.

## 8. Resultado para el equipo

Florinda consume una interfaz de dominio estable; cambiar baseURL, mock o backend no obliga a modificar componentes. Esta capa también centraliza observabilidad y tratamiento de sesión expirada.
