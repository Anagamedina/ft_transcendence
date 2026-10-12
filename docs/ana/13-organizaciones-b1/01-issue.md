# Issue 13 — B1: Organizaciones · GitHub #139 (parte B1) · incluye la #121

## 1. Objetivo

Que el admin gestione a sus clientes desde la app: verlos con sus números,
darlos de alta, editarlos, suspenderlos y llevar su prueba de 7 días.
Desbloquea las pantallas **Admin · Clientes** y **Ficha de cliente**, y la
B10 (registro público), que crea organizaciones en prueba.

## 2. Problema que resuelve

Hasta ahora el router de organizaciones estaba vacío: la única forma de
crear un cliente era el seed. La tabla ya tenía estado, prueba, contacto y
facturación (D1, Daruny), pero ninguna ruta los usaba.

## 3. Alcance

| Ruta | Qué |
|---|---|
| `GET /api/organizations` | Lista por nombre con contadores; filtros `q`, `status`, `has_open_alerts` |
| `POST /api/organizations` | Alta `ACTIVE`, con `first_site` opcional |
| `GET /api/organizations/{id}` | Ficha con contadores |
| `PATCH /api/organizations/{id}` | Nombre, contacto, facturación |
| `POST .../suspend` · `.../reactivate` | Cambiar el acceso |
| `POST .../extend-trial` · `.../activate` | Gestionar la prueba |

Y la regla de la issue: **una organización suspendida deja fuera a sus usuarios**.

## 4. Límites

- Sin `first_user`: los usuarios llegan por invitación (B4).
- Borrar organizaciones es la B16. Caducidad automática de la prueba, la B12.
- Usuarios desactivados (`is_active`), la B6.

## 5. Dependencias

B0 (#138) ✅ y D0+D1+D2 (#129) ✅. `TRIAL_DAYS` de la I0 (#151): mientras no
esté en `.env.example`, vale 7 por defecto.

## 6. Criterios de aceptación

- [x] Todas las rutas: 401 sin sesión, 403 con un cliente.
- [x] Listar, crear y editar con estado y contadores; contadores con `GROUP BY`.
- [x] Nombre repetido (también con otras mayúsculas) → 409; vacío → 422 `INVALID_NAME`; 120 caracteres se guarda.
- [x] Un cliente de una organización nueva no ve datos de nadie más (#121).
- [x] Una organización SUSPENDED impide entrar a sus usuarios.
