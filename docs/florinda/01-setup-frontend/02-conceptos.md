# Conceptos — Issue 01

## Modelo mental

Vite sirve/desarrolla y construye la SPA; Vue compone componentes; Router cambia la vista según URL; Tailwind aporta utilidades; DaisyUI aporta componentes visuales sobre Tailwind. Ninguna de estas piezas gestiona datos de negocio.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| SPA | Una aplicación que cambia vistas sin recarga completa | 20 min |
| Vue component | Template, estado, props y eventos | 30 min |
| Vite | Dev server, build y variables `VITE_*` | 25 min |
| Router | Rutas, layouts y navegación | 30 min |
| Tailwind | Utilidades y responsive breakpoints | 30 min |
| DaisyUI | Componentes y temas sobre Tailwind | 25 min |
| Layout | Estructura compartida de una zona | 20 min |

## Conceptos relacionados

Router decide qué componente se monta; layout decide cómo se presenta una zona. Un layout no debe realizar llamadas API ni contener reglas de autenticación todavía. DaisyUI acelera la apariencia, pero no reemplaza decisiones de accesibilidad ni responsive.

## Errores frecuentes

Mezclar rutas con componentes, abusar de estilos inline, importar CSS duplicado, depender de variables no definidas y poner lógica de API durante el setup.

## Conceptos en conjunto

### Build frente a desarrollo

El servidor de Vite facilita feedback local, pero la aplicación que se entrega es el resultado de `npm run build`. Una clase o variable que funciona en dev pero no se incluye en el build es un fallo de configuración, no de diseño visual.

### Router frente a layout

La ruta determina qué vista se monta; el layout aporta estructura común. Por eso las vistas Public no deben contener Sidebar de Admin y los layouts no deben conocer endpoints.

### Tailwind frente a DaisyUI

Tailwind aporta reglas pequeñas y DaisyUI componentes con apariencia coherente. Elegir una estrategia de temas evita mezclar colores arbitrarios y facilita cambiar la identidad visual.

## Qué debes poder demostrar

- Explicar qué ocurre desde `main.js` hasta la vista renderizada.
- Añadir una ruta sin modificar componentes no relacionados.
- Cambiar un token visual y verlo reflejado de forma consistente.
- Generar build y detectar una clase no incluida.
