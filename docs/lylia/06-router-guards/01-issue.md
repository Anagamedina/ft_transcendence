# Issue 06 — Guards y navegación por rol

## 1. Objetivo

Proteger rutas frontend según autenticación y rol, redirigiendo de forma coherente sin presentar el guard como sustituto de autorización backend.

## 2. Flujo esperado

```text
intento de ruta → cargar sesión → comprobar auth → comprobar rol → permitir/redirigir
```

## 3. Dependencias y límites

Depende de Auth Store, login/me y rol devuelto por backend; Florinda mantiene diseño Admin/Client. No incluye permisos backend.

## 4. Aprendizaje estimado

Navigation guards — 45 min; sesión async — 30 min; RBAC frontend — 30 min; redirect loops — 30 min; pruebas — 60 min.

## 5. Finalidad

Evita navegación accidental y mejora UX, mientras backend sigue protegiendo datos.

## 6. Criterios de aceptación

- [ ] Anónimo no entra en rutas privadas.
- [ ] CLIENT no entra en Admin.
- [ ] ADMIN llega a su zona.
- [ ] Refresh restaura sesión si procede.
- [ ] Logout bloquea acceso posterior.
- [ ] No existen loops de redirección.

## 6. Casos límite

Sesión todavía cargando, rol ausente, token expirado, ruta desconocida y URL original que debe conservarse.

## 7. Decisiones técnicas

- El estado `loading` no debe decidir como si fuera anónimo.
- Las rutas declaran requisitos mediante metadata explícita.
- Guard frontend mejora UX; backend repite autorización.

## 8. Resultado para el proyecto

La navegación refleja sesión y rol sin crear una falsa barrera de seguridad.
