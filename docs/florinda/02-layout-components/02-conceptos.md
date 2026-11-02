# Conceptos — Issue 02

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Composición | Construir UI combinando componentes | 25 min |
| Props | Datos que entran al componente | 20 min |
| Emits | Eventos que salen del componente | 20 min |
| Slots | Contenido flexible dentro de un componente | 25 min |
| Presentacional | UI sin conocimiento de API/store | 25 min |
| Responsive | Adaptación a viewport y navegación | 30 min |
| Focus/accessibility | Uso con teclado y lectores | 30 min |

## Conceptos relacionados

Props configuran Card/Modal; emits comunican acciones; slots permiten layouts sin duplicar markup. Un componente compartido debe ser más general que una vista, pero no tan abstracto que nadie entienda cómo usarlo.

La accesibilidad no es un paso final: botones, modal, foco y landmarks deben diseñarse desde el comienzo.

## Errores frecuentes

Componentes con nombres de negocio rígidos, props booleanas confusas, modal sin cierre por Escape, sidebar sin foco y estilos copiados.

## Conceptos en conjunto

Un layout define composición; un componente compartido define una pieza; una vista combina ambos. Si Card conoce `Sensor` o Modal conoce `/api`, deja de ser reusable.

Los slots son apropiados cuando la estructura es estable pero el contenido cambia. Las props son apropiadas cuando el componente necesita datos simples. Los emits son apropiados cuando comunica una acción sin decidir qué hará el padre.

## Qué debes poder demostrar

- Montar la misma Card con dos contenidos diferentes.
- Abrir/cerrar Modal sin conocer su implementación.
- Navegar Sidebar con teclado.
- Explicar qué comportamiento pertenece al padre y cuál al componente.
