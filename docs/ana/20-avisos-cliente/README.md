# #275 · Avisos automáticos al cliente

Issue: https://github.com/Anagamedina/ft_transcendence/issues/275 (Ana).
Tabla `alert_notifications`: #276 (Daruny).
Diseño: https://claude.ai/artifact/2ZKLbiFk9vFxegkfwAxRzE (tabla y panel con avisos).

## Por qué

Nuestro servicio es avisar a tiempo. Si salta una crítica y nadie del cliente
tiene la app abierta, hoy nadie se entera. Si sigue «Sin atender», el sistema
envía emails y, si nadie responde, AquaGuard llama.

| Urgencia | Aviso 1 | Aviso 2 | Después |
|---|---|---|---|
| Crítica | email a los 5 min | email a los 20 min | a los 45 min, AquaGuard llama |
| Leve | email a los 60 min | — | — |

«Me encargo» o cerrar la alerta para los avisos.

## Paso 1 · Frontend (rama `ana/275-avisos-cliente`)

Se hace antes que el backend y **no enseña nada hasta que el backend mande
`notifications`** en cada alerta: sin ese campo, la tabla y el panel quedan
como en #252.

| Pieza | Archivo | Qué hace |
|---|---|---|
| Pasos | `utils/notificationSteps.js` | `notificationSteps(alert, now)`: salta la alerta → emails (hecho ✓, siguiente «en 9 min», pendiente) → llamar. Si alguien se encarga, acaba en «Nombre se encarga». `noticeSummary` da la línea de la tabla («1 aviso · el 2.º en 9 min», «2 avisos · llamar»). El calendario (`SCHEDULE`) es el mismo de la issue |
| Línea de tiempo | `components/alerts/AlertNotificationsTimeline.vue` | «Avisos al cliente» en el panel: línea vertical continua hasta el último paso hecho y discontinua después; el siguiente en azul, «llamar» en granate |
| Tabla | `components/alerts/AdminAlertsTable.vue` | En «Sin atender», la columna «Quién se ocupa» (siempre «Nadie») pasa a «Avisos al cliente»; la fila que pide llamar se tiñe de rosa |
| Panel y vista | `AlertDetailPanel.vue`, `views/admin/AlertsView.vue` | El panel recibe `now` y, en cada refresco (60 s), los datos nuevos de su alerta: la línea avanza sola |

Tests: `src/utils/notificationSteps.test.js` (9).

Lo que espera del backend, en cada alerta:

```json
"notifications": [
  { "attempt": 1, "channel": "EMAIL", "recipient": "admin@cliente.es", "sent_at": "2026-10-25T10:05:00Z" }
]
```

## Paso 2 · Backend con tabla provisional (misma rama)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Tabla | `alerts/model.py` (`AlertNotification`), migración `e3b8c1f5a7d9` | `alert_notifications`: `alert_id`, `attempt`, `channel` (EMAIL), `recipient`, `sent_at`. `UNIQUE (alert_id, attempt)`, borrado en cascada. **Provisional**: es la de #276 (Daruny); cuando haga la suya, se queda la de él |
| Envío | `alerts/notices.py` (`enviar_avisos`) | Busca alertas ACTIVE sin «Me encargo» y envía el email que toque. 1.º al contacto de la organización (si no hay, a los usuarios); 2.º al contacto y a los usuarios activos. Uno por vuelta y por alerta. Se apunta **antes** de enviar: nunca se repite; si el proceso muere entre medias, ese se pierde |
| Cada minuto | `alerts/vigilante.py` (`una_vuelta_de_avisos`) | Misma vuelta que los sensores mudos, con su propia sesión y su propio `try` |
| API | `alerts/schemas.py`, `service.py`, `repository.py` | `notifications` (lista) y `next_notification_at` en cada alerta, cargados en bloque (`selectinload`) |

Tests: `tests/test_avisos_cliente_275.py` (13): calendario, a quién, uno por
vuelta, «Me encargo» y cerrar paran, nunca dos veces (también la base), API.

Probado en la demo: la migración se aplica sola al arrancar y Mailpit
(http://localhost:8025) recibe el email.

## Paso 3 · Revisión visual de la página (misma rama)

Lienzo: https://claude.ai/artifact/2ZKLbiFk9vFxegkfwAxRzE («Alertas corregida»).

- Tarjetas de clientes: reparten el ancho (nombre entero), «1 abierta · 1 crítica» en vez de la barra, «1 sensor» en singular y en una línea, la elegida solo con borde azul.
- Pestañas: «Arregladas» con su número en píldora, como las demás.
- Urgencia: selector segmentado (Todas | Críticas | Leves).
- Tabla: «Fallo» más ancha y sin partir; con un cliente filtrado, la columna pasa a «Edificio · planta»; en «Sin atender» no hay «Quién se ocupa» (siempre «Nadie»): sale «Avisos al cliente» cuando hay avisos; el reloj es un icono, no un emoji.
- Cabecera: «Actualizado hace…» centrado con el título.

## Decisiones

- **Sin botón «Avisar ya»**: confundía (parece llamar). Si a AquaGuard le
  preocupa una alerta, llama.
- **La hora de los pasos pendientes se calcula en el navegador** con el mismo
  calendario que el backend. Si el backend cambia los tiempos, hay que cambiar
  `SCHEDULE` (o que la API devuelva `next_notification_at` y usarlo).

## Pendiente

- Cambiar la tabla provisional por la de #276 cuando Daruny la haga (o que
  #276 sea revisar esta).
- La llamada de AquaGuard (paso 4) no se apunta en ningún sitio todavía.
