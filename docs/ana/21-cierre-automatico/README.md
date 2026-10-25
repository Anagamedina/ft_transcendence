# #277 · Cierre automático de alertas por las lecturas

Issue: https://github.com/Anagamedina/ft_transcendence/issues/277 (Ana).
Negocio y defensa: https://claude.ai/artifact/5bLVi4ympHnc5FS1QYTC3A (sección 10).

## Por qué

Si el cliente arregla la avería, las lecturas lo reflejan en segundos: son la
prueba. Antes (decisión del 28-09) una alerta no se cerraba nunca sola y se
acumulaban abiertas aunque el agua ya fuera bien. Decidido el 25-10: **las
lecturas cierran; el botón es la excepción.** La bajada corta ya no se pierde:
el cliente recibió los avisos (#275) y la alerta queda en «Arregladas» con su
línea de tiempo.

## La regla

| Alerta | Se cierra cuando… | `resolved_at` |
|---|---|---|
| Presión baja o alta | 15 min seguidos sin lecturas fuera de rango | la primera lectura normal |
| Sensor sin conexión | 15 min enviando lecturas otra vez | la primera lectura que vuelve |

- Los 15 minutos son de **confirmación**: por eso la hora de cierre es la de la
  primera lectura normal. «Tardó» y la mediana de resolución son reales.
- Solo con un sensor que sigue enviando (última lectura de hace menos de 5 min).
- Mientras se confirma **no se avisa al cliente**; si vuelve a ir mal, la cuenta
  empieza de cero y los avisos siguen donde estaban.
- Umbrales actuales del sensor: si el admin corrige un límite mal puesto, las
  lecturas siguientes ya cuentan como normales.
- `resolved_by` vacío = «por las lecturas».

## Qué se ha hecho (rama `ana/277-cierre-automatico`, sobre la de #275)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Regla | `alerts/autoclose.py` | `normal_desde(alerta)`: primera lectura después de la última fuera de rango (por `created_at`, índice `ix_readings_sensor_created_at`). `cerrar_por_lecturas`: cierra las que llevan 15 min |
| Cada minuto | `alerts/vigilante.py` | `una_vuelta_de_cierres`, antes de los avisos: no se avisa de lo que ya está arreglado |
| Avisos | `alerts/notices.py` | No envía si `normal_desde` no es nulo |
| API | `alerts/schemas.py`, `service.py` | `normal_since` y `closes_at`; `next_notification_at` nulo mientras se confirma |
| Panel | `AlertDetailPanel.vue` | Sin botón azul: «Ver sensor» abajo y «Cerrar a mano…» discreto, con su confirmación |
| Línea de tiempo | `utils/notificationSteps.js`, `AlertNotificationsTimeline.vue` | Paso verde «Normal desde las 10:32 · se cerrará sola a las 10:47»; al cerrar, «Arreglada: las lecturas lo confirman» o «Cerrada a mano por …» |
| Tabla | `AdminAlertsTable.vue` | En «Sin atender»: «Presión normal · se cierra sola en 12 min» |

Tests: `backend/tests/test_cierre_automatico_277.py` (10) y 3 en
`frontend/src/utils/notificationSteps.test.js`. Comprobado cambiando la hora de
cierre por la de confirmación: fallan 3 tests.

## A tener en cuenta

- La API calcula `normal_since` por cada alerta abierta (hasta 3 consultas
  pequeñas con índice). Con muchas alertas abiertas a la vez se podría agrupar.
- Una fuga intermitente (20 min bien, luego mal) cierra la alerta y abre otra
  nueva. Pendiente: marcar «se repite» si vuelve en menos de 24 h.

## Revisión del responsive (misma rama)

Comprobado con Playwright a 375, 768, 1024 y 1440 px (sin scroll lateral en ninguno):

- **Tabla solo desde `xl` (1280 px).** Con el menú lateral (16rem), entre 768 y
  1279 px la tabla no cabía y se cortaban «Avisos al cliente» y «Sin atender
  desde». Por debajo de `xl` se ven tarjetas, que ahora también llevan la línea de avisos.
- **Pestañas en una línea en el móvil**: más compactas por debajo de `sm`; caben
  desde 375 px y en pantallas más estrechas se desplazan dentro de su franja.
- **Tarjetas de clientes**: el número y «abiertas» en una línea, críticas y leves
  debajo (antes se partía «3 / abiertas · 2 críticas · 1 leve»); «+ 1 cliente» en singular.
- **Panel lateral por encima del botón ☰ del menú** del móvil (`z-[70]` frente a `z-[60]`), que tapaba «Crítica».
- **Pie del menú**: nombre y «Cerrar sesión» en líneas separadas, sin el «·» suelto.
