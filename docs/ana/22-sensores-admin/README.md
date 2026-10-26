# #283 · Sensores del admin: mantenimiento

Issue: https://github.com/Anagamedina/ft_transcendence/issues/283 (Ana).
Hablado con Florinda: la página era suya (#169) y la vista por plantas pasa a su ficha de edificio (#265).

## Por qué

AquaGuard instala y mantiene los sensores (vienen con el plan), así que la
página va **del aparato**, no del agua (eso es Alertas). Responde a «¿qué hay
que hacer en los edificios?». Antes tenía dos partes que no se hablaban
(un edificio con sus plantas arriba y una tabla de todos abajo).

## Qué se ve

Arriba, tres tarjetas que hacen de pestañas (cabecera B del lienzo): el
número, un icono y una frase («el más antiguo, hace 10 h», «en 5 edificios»,
«7 funcionan»).

| Pestaña | Qué es | Qué hacer |
|---|---|---|
| **Sin conexión** | Los sensores que dejaron de enviar, **agrupados por edificio** (el cliente en pequeño, el edificio como título y en cada fila primero la planta) y el más callado primero: «más de 6 h» / «más de 1 h», la hora de la última lectura y lo que marcaba, y «hace X» grande (sin barras: propuesta 10 A). Si caen varios a la vez en un edificio, «puede ser la wifi del edificio». Los que **nunca han enviado** no salen aquí (no es una avería): se ven en su edificio como «nunca ha enviado» / «sin estrenar» | «Avisar al cliente» abre un email ya escrito (el admin no va al edificio) |
| **Plantas sin sensor** | Por edificio, las plantas sin ningún sensor, «4 de 10 con sensor» | «+ Instalar aquí» abre el formulario con el edificio y la planta |
| **Sensores** | Diseño **A + C**: a la izquierda, los clientes en filas compactas, en dos grupos: **«Necesitan atención»** (icono ámbar si es la presión, gris si es «sin conexión», qué pasa en pocas palabras y «2 de 4 funcionan») y **«Funcionan bien»**, más discreto. La lista va sobre gris y el cliente elegido, en blanco, se une a su ficha de la derecha, como una pestaña de carpeta. A la derecha, el cliente elegido: su nombre como título, «2 edificios · 4 de 5 sensores funcionan · teléfono» y «Avisar al cliente»; debajo, **todos sus edificios seguidos**, cada uno con su título, «2 de 3 funcionan · 1 sin estrenar · 1 planta sin sensor», «+ Añadir sensor» y la tabla de sus plantas de arriba abajo (Planta · Sensor · Ahora · Normal entre · Estado), con «+ Dar de alta» en las vacías. En el móvil, primero la lista y después el cliente con «‹», con las plantas en dos líneas | Pulsar una fila abre el panel |

Al pulsar un sensor se abre el **panel lateral**, como en Alertas: lo
importante arriba («Presión alta · 4,8 bar · máximo 4,5 · el aparato
funciona»; la etiqueta de arriba dice «Envía lecturas», no «Funciona»), la **gráfica con 24 h · 7 días · 30 días** (la
`PressureChart` de Florinda con los puntos de `/readings/series`), umbrales,
última lectura, fecha de alta, alertas con enlace a Alertas, contacto, las
tres **últimas alertas** del sensor y «Ajustar umbrales»
(el `SensorForm` de siempre). «+ Añadir sensor» (en la ficha del cliente), «+ Dar de alta» (en una planta vacía) y «+ Instalar aquí» usan el
mismo panel.

## Piezas

| Pieza | Archivo |
|---|---|
| Página | `views/admin/SensorsView.vue` (pestaña, búsqueda, orden, `?site=` y `?sensor=` en la URL; refresco cada 60 s) |
| Cabecera | `components/sensors/SensorTabCards.vue` (tarjetas con `role="tab"`, flechas para moverse) |
| Sin conexión | `components/sensors/OfflineByBuilding.vue` |
| Plantas sin sensor | `components/sensors/MissingFloorsList.vue` |
| Clientes | `components/sensors/SensorClientList.vue` |
| Cliente elegido | `components/sensors/SensorClientDetail.vue` (`?client=` en la URL) |
| Panel | `components/sensors/SensorSidePanel.vue` |
| Lógica | `utils/sensorMaintenance.js` (`splitOffline`, `groupBySite`, `silenceBadge`, `noticeMailto`, `floorsWithoutSensor`, `sensorTree`, `clientIssue`, `needsAttention`, `alertsPerSensor`, `TOO_MANY_ALERTS`) |
| Datos extra | `stores/adminSensors.js` (alertas de 7 días, contactos, series con caché de un minuto) |

Los sensores y los edificios salen de `stores/sensors.js` y `stores/sites.js`
(todos, página a página): las tres pestañas cuentan sobre los mismos datos y
crear o editar un sensor las actualiza a la vez. Las alertas de 7 días y los
contactos también se piden página a página (antes se cortaban en 100), y el
refresco de cada minuto lo recarga todo: sensores, edificios, alertas y
contactos (revisión de Daru). «Ver sensor» desde Alertas
abre ese sensor (`?sensor=`).

Diseños: cabecera y «Sin conexión» en https://claude.ai/artifact/AxUPNXvKDJjZbXS6VoxxJX
(cabecera B, 9 y 10 A); la pestaña Sensores en https://claude.ai/artifact/3UqktyWhMoKTWT7CnxNZUB (A + C, de las ideas de https://claude.ai/artifact/2VNuFeW5uw6TY7PXu9B4Vs), con el cliente unido a su ficha y todos sus edificios seguidos (propuesta 3 de https://claude.ai/artifact/UAA79ju8CkCt757LCGbUSS).

Tests: `src/utils/sensorMaintenance.test.js` (17). Comprobado con Playwright a
1440 y 390 px (sin scroll lateral), con el panel abierto.

## Pendiente

- «Desactivar» un sensor: la API no deja cambiar `is_active`.
- «Por instalar según contrato»: depende de #274 (lo contratado).
- Batería y revisiones: no hay datos.
- Los 9 sensores «Demo avisos» de `make seed-avisos` salen como «nunca ha enviado» / «sin estrenar».
- Ya no hay «+ Nuevo sensor» arriba: siempre se da de alta en un edificio elegido.
- «Avisado hoy a las…»: guardar el aviso necesita backend (como en #275); de momento solo `mailto`.
- Al dar de alta, copiar el umbral de las otras plantas del edificio (lo enseña el diseño 2).
