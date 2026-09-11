# Verificación — Issue 04

Este documento recoge la verificación real de la Fase 3 de `04-implementacion.md`, de los criterios de aceptación de `01-issue.md` y de lo exigido en "Qué debes poder demostrar" de `02-conceptos.md`.

## Checklist Fase 3 (04-implementacion.md)

- [x] **Navegar sin sesión.** La Landing carga completa en `/` sin requerir autenticación; no hay ninguna llamada a API ni guard de sesión bloqueando el acceso.
- [x] **Probar cada CTA y refresh directo de ruta.** Ver detalle en la sección "Refresh directo" más abajo.
- [x] **Revisar móvil/desktop, teclado, contraste y consola.** Probado en 82px (protegido con `overflow-x-hidden`), 346px, 375px, 414px, 768px, 1024px, 1440px+ y rotación horizontal. Navegación con Tab: orden correcto, foco visible en todos los elementos. Contraste: tarjetas 10.31:1 (AAA); Hero con `drop-shadow` como refuerzo sobre el degradado. Consola sin excepciones (ver detalle abajo).

## Refresh directo de rutas (caso 7, `01-issue.md`)

Probado en Chrome y Firefox escribiendo la URL directamente y pulsando los CTA "Iniciar sesión" y "Registrarse" (el CTA "Comenzar ahora" del Hero también se probó, pero lleva a la misma ruta `/registro` que "Registrarse", no añade una ruta distinta):

- `/login` y `/registro` cargan en blanco, **sin ninguna excepción de JavaScript**.
- Único mensaje en consola: `[Vue Router warn]: No match found for location with path "/login"` (y equivalente para `/registro`), esperado porque esas rutas pertenecen al issue #35 ("[FRONTEND][MANDATORY] Implementar Login, Registro y Logout"), actualmente en *Backlog* sin iteración asignada.
- Único error real: 404 de `favicon.ico`, ajeno a este issue (falta configurar favicon en el proyecto).

## Otros casos contemplados (sección 7, `01-issue.md`)

| Caso | Resultado |
|---|---|
| Usuario que entra directamente a `/` | OK — Landing completa sin sesión |
| Navegación con teclado hasta ambos CTA | OK — foco visible, orden correcto |
| Pantalla pequeña sin CTA fuera del viewport | OK — probado desde 82px con `overflow-x-hidden` |
| Imagen ausente o lenta sin romper el contenido | No aplica — no se usan imágenes externas; el Hero usa CSS puro (`.water-drop-lg`) y los iconos son SVG propios inline |
| Refresh directo de Login/Registro | OK — ver sección anterior |

## Qué debes poder demostrar (02-conceptos.md)

- **Explicar el recorrido de un visitante nuevo:** entra a `/`, ve el Hero (propuesta de valor), baja a "Cada gota, bajo control" (funcionalidades), y decide ir a Login/Registro o quedarse leyendo — recorrido coincide con el diagrama de `03-diagrama.md`.
- **Identificar el CTA principal y secundario:** principal = "Comenzar ahora" (Hero, lleva a `/registro`); secundarios = "Iniciar sesión" y "Registrarse" en el Header, visibles en todo momento.
- **Navegar toda la Landing sin ratón:** confirmado por Tab, orden lógico Header → Hero CTA → tarjetas → Footer.
- **Validar que el mensaje permanece legible en móvil:** confirmado en los breakpoints probados; el texto del Hero mantiene contraste AAA sobre el degradado sólido en todos los anchos.

## Comprensión del mensaje (criterio de entrega, `04-implementacion.md`)

Se hizo una prueba real con una persona ajena al proyecto AquaGuard, enseñándole la Landing sin contexto previo:

- **Copy original** ("El agua es vida, y cada gota cuenta."): la persona navegó y encontró los botones sin problema, pero **no supo explicar qué hace el producto** — entendió que "iba de agua" pero no identificó la detección de fugas como función principal.
- **Copy iterado** (titular "Detecta las fugas de agua antes de que sean un problema.", subtítulo con mención explícita a sensores y alertas): mejora clara a juicio propio tras revisar el resultado en pantalla, pero **no se repitió la prueba con una persona externa sobre este copy definitivo**. Este punto queda abierto como buena práctica antes de dar el mensaje por validado al 100%, aunque no se considera bloqueante para cerrar el issue.

### Efecto en cascada del cambio de copy sobre el layout

El cambio de texto del Hero (titular más largo, subtítulo más largo) obligó a una serie de ajustes de layout no anticipados inicialmente:
- Salto de línea manual (`<br>`) en el titular para controlar dónde rompe en distintos anchos.
- Rediseño de la rejilla del Hero (`grid-cols-[1fr_2fr]` → `grid-cols-[auto_1fr]`) porque el texto más largo necesitaba más espacio horizontal, lo que a su vez obligó a reposicionar la gota decorativa (`order`, `justify-start`).
- Ajuste de padding inferior (`pb-24` → `pb-32 md:pb-24`) y escala de la gota en móvil (`scale-75 md:scale-100`), porque el bloque de texto más alto empujaba el botón hacia la onda SVG inferior.
- Descubrimiento de un bug de clic no relacionado directamente con el texto pero destapado por este proceso de ajuste: el SVG decorativo de la onda bloqueaba los clics sobre el CTA "Comenzar ahora" por estar posicionado encima en el orden de apilado, aunque visualmente no lo tapara. Solucionado con `pointer-events-none` en el SVG.

**Lección para el equipo**: un cambio de copy en el Hero (o en cualquier bloque con layout ajustado a mano) no es un cambio "solo de texto". Cambiar la longitud del texto puede romper el espaciado, la posición de elementos decorativos, y en este caso concreto llegó a enmascarar un bug de interacción real. **Cualquier futura modificación del texto del Hero debe repetir el checklist completo de este documento** (responsive en todos los breakpoints, teclado, consola, y clic real en los CTA — no solo mirar que el texto quepa visualmente), no solo una revisión de contenido.

## Pendiente de re-verificar cuando el issue #35 se mergee

El issue #35 ("[FRONTEND][MANDATORY] Implementar Login, Registro y Logout") está en *Backlog* a fecha de este documento. No bloquea el cierre del Issue 04/#5, pero cuando se mergee a `develop` hay que repetir esta verificación de integración (10-15 min, no desarrollo nuevo):

1. Actualizar la rama/`develop` local y repetir el refresh directo de `/login` y `/registro` — debe cargar el contenido real de Lylia, sin el warning de Vue Router documentado arriba.
2. Confirmar que los `RouterLink` del Header/PublicLayout siguen llevando a la vista correcta.
3. Revisar que `PublicLayout` (Header degradado + Footer dark) encaja bien con las vistas de Login/Registro, especialmente si Lylia modificó `Header`/`Footer`/`Card`.
4. Sustituir la referencia a "#35 en Backlog" en este documento por confirmación de integración probada, con fecha (esto no afecta al ADR `0003`, que no menciona el issue #35).
5. Revisar consola una última vez: solo entonces el criterio "no hay errores ni warnings relevantes" queda cumplido al 100%, no solo justificado.

## Conclusión

Los tres puntos de la Fase 3 y los cinco casos de la sección 7 del issue quedan verificados. El bug de clic en el CTA (SVG decorativo bloqueando el botón) quedó detectado y solucionado durante esta misma verificación. No hay bloqueantes. El único punto fuera del alcance de este issue (rutas `/login`/`/registro` sin implementar) está documentado y referenciado al issue #35 correspondiente.

**Issue dado por finalizado** con una salvedad explícita: el copy definitivo del Hero mejora la comprensión a juicio del equipo, pero no se validó formalmente con una segunda prueba externa. Ver la sección "Comprensión del mensaje" para el detalle y la advertencia sobre futuras modificaciones de texto.