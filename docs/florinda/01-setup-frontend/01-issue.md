# Issue 01 — Setup de Vue, Vite, Router, Tailwind y DaisyUI

## 1. Objetivo

Preparar la base técnica y visual del frontend de AquaGuard: aplicación Vue 3 ejecutable, navegación inicial y sistema de estilos consistente.

## 2. Problema que resuelve

Sin una base acordada, cada vista configura estilos, rutas y estructura de forma diferente. Esta issue crea el suelo común sobre el que trabajarán las siguientes vistas.

## 3. Requisitos y límites

Configurar Vue/Vite, Vue Router, Tailwind, DaisyUI, vistas Public/Admin/Client y layouts iniciales. No incluye Pinia, Axios, services, auth store ni integración API de User04.

## 4. Dependencias y aprendizaje

No depende de otras issues. Vue/Vite — 45 min; Router — 30 min; Tailwind/DaisyUI — 60 min; estructura de vistas — 45 min; verificación — 30–45 min.

## 5. Finalidad

Es el punto de entrada de todo el frontend y fija la convención de carpetas, imports y estilos.

## 6. Criterios de aceptación

- [x] La aplicación arranca sin errores.
- [ ] Router navega entre Public, Admin y Client. *(en el merge original solo existía la Zona Pública; Admin/Client llegan con vistas posteriores)*
- [ ] Tailwind y DaisyUI generan estilos utilizables. *(no funcionó nunca en el proyecto real: `postcss.config.js` era el placeholder de Daruny desde el commit original; la captura que parecía demostrar lo contrario era de un HTML aparte con Tailwind vía CDN, no de la app real — corregido de forma definitiva en el Issue 02/#3)*
- [ ] Vistas y layouts base existen. *(solo `LandingView.vue`; los layouts reales — `MainLayout`/`PublicLayout` — se construyeron en el Issue 02/#3)*
- [ ] No hay errores/warnings relevantes de consola. *(no verificado formalmente en su momento; sin Tailwind funcional tampoco se habría detectado a simple vista)*

## 6. Decisiones técnicas

- Router concentra navegación; las vistas no cambian URL manualmente.
- Layouts definen zonas de interfaz, no datos de negocio.
- Tailwind es la fuente de utilidades; DaisyUI se usa como extensión, no como estilos duplicados.
- La configuración debe funcionar igual en desarrollo y build.

## 7. Resultado para el equipo

Florinda puede construir vistas sobre rutas y componentes previsibles. User04 podrá añadir Pinia, services y auth sin rehacer la estructura visual.

## 8. Casos que deben contemplarse

- Recarga directa de una ruta.
- Ruta desconocida.
- Vista dentro de cada layout.
- Build de producción sin clases desaparecidas.
- Navegación móvil sin perder acceso al contenido.
