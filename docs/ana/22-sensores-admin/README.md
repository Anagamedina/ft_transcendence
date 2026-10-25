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
| **Sin conexión** | Los sensores que dejaron de enviar, **agrupados por edificio** y el más callado primero: «más de 6 h» / «más de 1 h», la hora de la última lectura y lo que marcaba, y «hace X» grande (sin barras: propuesta 10 A). Si caen varios a la vez en un edificio, «puede ser la wifi del edificio». Los que **nunca han enviado** van plegados abajo: no es una avería | «Avisar al cliente» abre un email ya escrito (el admin no va al edificio) |
| **Plantas sin sensor** | Por edificio, las plantas sin ningún sensor, «4 de 10 con sensor» | «+ Instalar aquí» abre el formulario con el edificio y la planta |
| **Sensores** | **Árbol cliente › edificio** que se despliega (propuesta 1 del lienzo nuevo) con, dentro de cada edificio, **la tabla de la propuesta 3**: Planta · Sensor · Ahora · Normal entre · Estado («funciona», «baja · 1 alerta en 7 días», «sin conexión · 12 h», «nunca ha enviado»), todas las plantas de arriba abajo y «+ Dar de alta» en las vacías. «Con problemas primero» o «Cliente A–Z». Se abren solos los clientes y edificios con algo que mirar («nunca ha enviado» no cuenta, igual que en la tarjeta de arriba) | Pulsar una fila abre el panel |

Al pulsar un sensor se abre el **panel lateral**, como en Alertas: lo
importante arriba, la **gráfica con 24 h · 7 días · 30 días** (la
`PressureChart` de Florinda con los puntos de `/readings/series`), umbrales,
fecha de alta, alertas con enlace a Alertas, contacto y «Ajustar umbrales»
(el `SensorForm` de siempre). «+ Nuevo sensor» y «+ Dar de alta» usan el
mismo panel.

## Piezas

| Pieza | Archivo |
|---|---|
| Página | `views/admin/SensorsView.vue` (pestaña, búsqueda, orden, `?site=` y `?sensor=` en la URL; refresco cada 60 s) |
| Cabecera | `components/sensors/SensorTabCards.vue` (tarjetas con `role="tab"`, flechas para moverse) |
| Sin conexión | `components/sensors/OfflineByBuilding.vue` |
| Plantas sin sensor | `components/sensors/MissingFloorsList.vue` |
| Árbol | `components/sensors/SensorTree.vue` (`<details>` por cliente y edificio, una tabla por edificio que se desplaza dentro de su caja en el móvil) |
| Panel | `components/sensors/SensorSidePanel.vue` |
| Lógica | `utils/sensorMaintenance.js` (`splitOffline`, `groupBySite`, `silenceBadge`, `noticeMailto`, `floorsWithoutSensor`, `sensorTree`, `needsAttention`, `alertsPerSensor`, `TOO_MANY_ALERTS`) |
| Datos extra | `stores/adminSensors.js` (alertas de 7 días, contactos, series con caché de un minuto) |

Los sensores y los edificios salen de `stores/sensors.js` y `stores/sites.js`
(todos, página a página): las tres pestañas cuentan sobre los mismos datos y
crear o editar un sensor las actualiza a la vez. «Ver sensor» desde Alertas
abre ese sensor (`?sensor=`).

Diseños: cabecera y «Sin conexión» en https://claude.ai/artifact/AxUPNXvKDJjZbXS6VoxxJX
(cabecera B, 9 y 10 A); el árbol en https://claude.ai/artifact/MY5xMfa1aiJAukDFtG6QWR (propuesta 1 con la tabla de la 3).

Tests: `src/utils/sensorMaintenance.test.js` (13). Comprobado con Playwright a
1440 y 390 px (sin scroll lateral), con el panel abierto.

## Pendiente

- «Desactivar» un sensor: la API no deja cambiar `is_active`.
- «Por instalar según contrato»: depende de #274 (lo contratado).
- Batería y revisiones: no hay datos.
- Los 9 sensores «Demo avisos» de `make seed-avisos` salen en «nunca han enviado».
- «Avisado hoy a las…»: guardar el aviso necesita backend (como en #275); de momento solo `mailto`.
- Al dar de alta, copiar el umbral de las otras plantas del edificio (lo enseña el diseño 2).
