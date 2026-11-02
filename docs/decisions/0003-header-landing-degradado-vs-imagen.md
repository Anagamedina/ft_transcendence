# 0003 — Header de Landing: degradado en vez de imagen, y extensión de componentes compartidos

**Fecha:** 9 de septiembre de 2026
**Issue:** #5
**Autora:** Florinda (Frontend Lead — Public & Admin)
**Estado:** Implementado, pendiente merge a `develop`

## Contexto

El Issue #5 pedía la Landing Page pública (Zona Pública, ver §7 de "AquaGuard - Requisitos y arquitectura"). Los componentes base (`Header`, `Footer`, `Card`) ya existían desde el Issue #3, pero estaban pensados sin distinguir Zona Pública de Admin/Client, así que hubo que extenderlos sin romper su uso en las otras zonas.

## Decisiones tomadas

### 1. Fondo del Header: degradado en vez de imagen
Se probó `Aquaguard_header.jpg` con máscara/ondas para dar textura al Header. Se descartó por dos motivos:
- **Costuras visuales**: difíciles de resolver de forma consistente entre anchos de pantalla.
- **Contraste no garantizado (accesibilidad)**: al ser una fotografía con luminosidad y color variables por zonas, no se puede certificar una ratio de contraste mínima en todo punto donde el texto pueda caer. Como el layout es responsive, el texto se reposiciona sobre distintas zonas de la imagen según el breakpoint, por lo que el contraste podía pasar en una resolución y fallar en otra. El degradado sólido `from-[#0369A1] to-[#06B6D4]` con texto blanco da una ratio de contraste fija y medible en cualquier ancho, y además fusiona mejor visualmente con el Hero de la Landing.

Comparación visual confirmada entre ambas versiones (capturas del 9/9): la versión con foto carecía además de un CTA principal visible en el Hero ("Comenzar ahora"), y repetía el motivo de la gota tres veces (foto + gota decorativa + logo), compitiendo con el mensaje principal — motivo adicional a favor del degradado.

### 2. Extensión de componentes vía props/slots opcionales, no vía nuevos componentes
- `Header`: slot `actions` con fallback al botón "Menu" original — Admin/Client no necesitan cambios.
- `Footer`: prop `dark` (default `false`) — comportamiento por defecto sin cambios para Admin/Client. Además, el contenedor interno pasó de `max-w-7xl` a `w-full` (no a `max-w-6xl` como en una revisión anterior de este documento): decisión consciente para que Header y Footer actúen como "marcos" de ancho completo enmarcando el contenido, mientras que Hero y tarjetas quedan centrados en `max-w-6xl` como bloque de contenido. Es decir, Header/Footer no están pensados para alinearse con el ancho del contenido central, sino entre sí.
- `Card`: prop `showButton` (default `true`) y slot opcional `#icon` — uso existente en Admin/Client no se ve afectado.

Esto mantiene un único componente por elemento de UI compartido, evitando duplicación entre zonas, en línea con el principio de arquitectura frontend de "Public, Admin y Cliente compartirán componentes, estilos, servicios y estado para evitar duplicar código" (§3.2 del documento de arquitectura).

## Consecuencias

- Cualquier nueva zona (o vista pública adicional) puede reutilizar `Header`, `Footer` y `Card` pasando las props/slots ya definidos, sin tocar su implementación base.
- Si en el futuro se necesita un Header con imagen de fondo, habrá que resolver primero el problema de costuras y de contraste variable en distintos anchos antes de reabrir esa opción.