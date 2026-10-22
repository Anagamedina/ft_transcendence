# Issue 18 — Arranque en orden y rotación de logs

Corresponde a dos issues de GitHub que tocan el mismo archivo (`compose.yaml`)
y van en la misma PR:

* #243 (I7): arranque de los servicios en orden.
* #245 (I9): rotación de los logs de Docker.

## 1. Objetivo

* Que cada servicio espere a que el anterior esté **listo**, no solo arrancado.
* Que los logs de los contenedores no puedan llenar el disco.

## 2. Problema

**Orden.** El simulador dependía del backend con `condition: service_started`.
Docker lo arranca en cuanto existe el contenedor del backend, aunque la API
todavía no responda. El simulador ya esperaba a `/api/health/db` antes de
enviar, pero un `docker compose --profile sim up` directo o un reinicio del
backend dejaban una ventana con errores en los logs.

**Logs.** Docker guarda los logs de cada contenedor en un archivo sin límite.
Con el simulador enviando lecturas cada 5 s y el gateway registrando cada
petición, un stack encendido varios días ocupa gigas. Con el disco lleno,
PostgreSQL deja de escribir y los backups fallan.

## 3. Requisitos

* `simulator.depends_on.backend.condition: service_healthy`.
* El resto de `depends_on` también con `service_healthy`.
* `simulator/.dockerignore` sin `.env`, `.venv`, `__pycache__` ni tests.
* El simulador reintenta con espera si la API responde con error.
* Bloque común `x-logging` (json-file, 10 MB × 3) en todos los servicios.
* README actualizado.

## 4. No incluye

* Cambiar los healthchecks existentes.
* Cambiar la lógica del simulador.
* Logs centralizados (ELK es otro módulo).
