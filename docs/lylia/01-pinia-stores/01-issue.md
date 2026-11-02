# Issue 01 — Pinia y stores globales

## 1. Objetivo

Crear la capa de estado global del frontend para centralizar sesión, usuario, sensores y alertas sin duplicar estado dentro de componentes.

## 2. Problema que resuelve

Si cada vista guarda su propia copia de usuario o sensors, los cambios no se sincronizan y aparecen requests duplicadas. Pinia ofrece una fuente reactiva y explícita para datos compartidos.

## 3. Requisitos y límites

Instalar/configurar Pinia, crear stores y definir estados/acciones básicas. No incluye diseño visual, layouts, cards, Dashboard ni llamadas HTTP concretas de Axios.

## 4. Dependencias

Depende del setup Vue de Florinda. Debe coordinar nombres y shapes con User04 y backend. Services y adapters alimentarán los stores, pero no deben quedar mezclados con la UI.

## 5. Aprendizaje estimado

Reactividad Vue — 45 min; Pinia state/getters/actions — 60 min; persistencia de sesión — 45 min; separación store/service — 45 min; tests — 60 min.

## 6. Finalidad

Es la fuente de verdad compartida que permitirá que login, guards, dashboards y componentes reaccionen al mismo estado.

## 7. Criterios de aceptación

- [ ] Pinia está configurado en `main.js`.
- [ ] Existen stores de auth y dominios necesarios.
- [ ] Vistas pueden consumir stores reactivos.
- [ ] Acciones tienen responsabilidades claras.
- [ ] No se duplica estado en componentes.
- [ ] Stores no dependen de detalles visuales.

## 8. Decisiones técnicas

- Separar estado remoto de estado efímero de un formulario.
- No guardar tokens sensibles en lugares inseguros sin decisión documentada.
- Definir estados `idle/loading/success/error` para operaciones asíncronas.
- Evitar que un getter haga fetch.

## 9. Casos límite

Sesión ausente, logout, store reinicializado al refresh, request concurrente y error de carga parcial.
