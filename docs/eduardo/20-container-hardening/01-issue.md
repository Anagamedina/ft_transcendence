# Issue 20 — Endurecer los contenedores

Corresponde a la issue #246 de GitHub (I8). Sustituye a #95 y #86, que eran
duplicadas.

## 1. Objetivo

Que cada contenedor se ejecute con los mínimos permisos y recursos que
necesita.

## 2. Problema

El backend y el backup se ejecutaban como **root**. Si alguien encontrara una
vulnerabilidad en la API, tendría root dentro del contenedor y acceso a los
volúmenes de documentos y backups. Además, ningún servicio tenía límite de
memoria ni de CPU: un fallo en uno podía dejar sin recursos al resto.

## 3. Requisitos

* `backend/Dockerfile` y `backup/Dockerfile`: usuario sin privilegios con UID
  fijo y `USER`.
* En cada servicio de `compose.yaml`, cuando sea posible:
  `no-new-privileges`, `cap_drop: [ALL]` con `cap_add` solo para lo
  imprescindible, `read_only: true` con `tmpfs` para `/tmp`, y `mem_limit` y
  `cpus` medidos con `docker stats`.
* Que los volúmenes ya creados (`documents_data`, `backups_data`) sigan
  funcionando al dejar de usar root.
* README: sección corta de seguridad de los contenedores.

## 4. No incluye

* WAF/ModSecurity ni Vault (módulo de Cybersecurity).
* Escanear las imágenes en busca de vulnerabilidades.

## 5. Dependencias

I7 e I9 (#243, #245), ya mergeadas. Esta rama parte de la de I6 (#244) para
comprobar que `make backup-verify` funciona con los contenedores endurecidos.
