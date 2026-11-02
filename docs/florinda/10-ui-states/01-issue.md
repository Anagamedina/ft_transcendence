# Issue 07 — Loading, Error y EmptyState reutilizables

## 1. Objetivo

Crear estados visuales comunes para operaciones asíncronas y usarlos desde vistas/componentes sin repetir soluciones inconsistentes.

## 2. Modelo de estado

```text
idle → loading → ready
              ├→ empty
              └→ error → retry
```

## 3. Dependencias y límites

Depende de components/layouts de Florinda y de estados remotos de Lylia. No incluye Header, Sidebar, Cards ni Modal.

## 4. Aprendizaje estimado

Async UI — 30 min; estados discriminados — 30 min; accesibilidad/feedback — 30 min; integración — 60 min; pruebas — 45 min.

## 5. Finalidad

El usuario siempre recibe feedback claro y las vistas mantienen el mismo comportamiento.

## 6. Criterios de aceptación

- [ ] Los tres componentes son reutilizables.
- [ ] Reciben mensaje/acción por props o eventos.
- [ ] Se integran con stores/services.
- [ ] Empty no se confunde con error.
- [ ] Retry y foco son accesibles.

## 6. Casos límite

Error con retry, carga larga, lista vacía válida, respuesta parcial y transición rápida loading→error.

## 7. Decisiones técnicas

- Un estado debe ser mutuamente comprensible: no mostrar error y contenido obsoleto sin indicarlo.
- Retry debe repetir la action del store, no inventar una request en el componente.
- Mensajes y foco deben ser accesibles.

## 8. Resultado para el proyecto

Todas las vistas ofrecen feedback uniforme ante la naturaleza asíncrona de la API.
