# Issue 04 — Landing Page pública

## 1. Objetivo

Crear la página pública principal que explica AquaGuard y dirige claramente a Login y Registro, con una experiencia responsive y sin requerir autenticación.

## 2. Contenido y límites

Debe incluir propuesta de valor, funcionalidades principales, navegación visible, Header y Footer. No implementa login, registro, sesión ni llamadas API de User04.

## 3. Dependencias y aprendizaje

Depende de setup y componentes compartidos. Jerarquía visual/conversión — 30 min; responsive — 30 min; accesibilidad/SEO básico — 45 min; implementación — 60–90 min.

## 4. Finalidad

Es la primera impresión y entrada pública del producto. Debe ser entendible sin contexto técnico.

## 5. Criterios de aceptación

- [ ] Accesible sin autenticación.
- [ ] Explica claramente AquaGuard.
- [ ] Login y Registro navegan correctamente.
- [ ] Usa Header/Footer compartidos.
- [ ] Funciona en móvil, tablet y desktop.
- [ ] No genera errores/warnings relevantes.

## 6. Decisiones técnicas

- La propuesta de valor aparece antes que los detalles secundarios.
- Login y Registro son CTA visibles, pero su lógica pertenece a User04.
- La página usa componentes compartidos y contenido semántico.
- Las imágenes decorativas no deben competir con el mensaje principal.

## 7. Casos que deben contemplarse

- Usuario que entra directamente a `/`.
- Navegación con teclado hasta ambos CTA.
- Pantalla pequeña sin CTA fuera del viewport.
- Imagen ausente o lenta sin romper el contenido.
- Refresh directo de Login/Registro.
