# Verificación — Issue 11

> Verificado contra el repositorio el 2 de octubre de 2026, sobre la rama
> `feature/edu/21-health-smoke` partiendo de `develop`. Corresponde a la
> issue #21 de GitHub.

## 1. Qué se implementó

Los healthchecks ya estaban en `develop` cuando empezó esta issue: `database` y `backend` desde la #19, `gateway` desde la #20 y `simulator` desde la #89. Lo que faltaba era el smoke test.

* `scripts/smoke.sh`: fichero nuevo. Comprueba el stack de punta a punta y se para en el primer fallo.
* `Makefile`: target `smoke`.
* `README.md`: cómo ejecutar el smoke test y qué comprueba, `make smoke` en la tabla de comandos y una fila nueva en "Implemented features".

## 2. Qué comprueba el smoke test

En este orden:

1. `docker compose up -d --wait --wait-timeout 60` sobre `database`, `backend` y `gateway`: arranca los que estén parados y espera hasta 60 segundos a que los tres estén `healthy`.
2. `/api/health` responde.
3. `/api/health/db` responde, es decir, el backend llega a PostgreSQL.
4. `http://localhost/` responde 301, la redirección a HTTPS.
5. `https://localhost/` sirve el `index.html` de la SPA.
6. El sensor `SENS-001` del seed existe. Si no, pide `make seed`.
7. `POST /api/readings` acepta una lectura con un `id` nuevo.
8. Esa lectura está en la tabla `readings` de PostgreSQL. Después se borra.
9. Si el simulador está en marcha, ha llegado al menos una lectura en los últimos 30 segundos. Si no está en marcha, o está en el escenario `offline`, que no envía lecturas a propósito, se indica como `skip`, no como fallo.

## 3. Decisiones técnicas

**Un script lineal.** Cada comprobación es un comando seguido de `|| fail "mensaje"`: si el comando falla, el script imprime el mensaje y sale con código 1. No hay bucles ni lógica de reintentos propia. Una primera versión los tenía y quedaba demasiado difícil de leer y de defender. Todo lo que hacía se podía conseguir con herramientas estándar.

**Esperar con `docker compose up --wait`.** Es la opción oficial de Compose para esperar a que los healthchecks digan `healthy`, no solo `running`. Sustituye a un bucle propio con `docker inspect` y un tiempo límite. Como efecto secundario, si un servicio está parado lo arranca. Si no consigue dejarlo sano en 60 segundos, falla.

**`curl -f` para comprobar respuestas.** Con `-f`, `curl` devuelve error si el servidor responde 400 o más, así que no hace falta leer el código HTTP a mano. `-s` quita la barra de progreso y `-k` acepta el certificado autofirmado.

**El healthcheck del backend sigue siendo de liveness.** Usa `/api/health`, que no consulta PostgreSQL. Si usara `/api/health/db`, una caída de la base marcaría el backend como `unhealthy` y, con `restart: unless-stopped`, podría acabar en reinicios en bucle que no arreglan nada. La readiness según la base la comprueba el smoke test con `/api/health/db`.

**Una lectura propia, identificada por su `id`.** `POST /api/readings` acepta un `id` opcional. El script genera un UUID nuevo en cada ejecución con `/proc/sys/kernel/random/uuid`, así que repetir el test nunca choca con una ejecución anterior, y la comprobación en PostgreSQL busca exactamente esa lectura. La presión es 3,5 bar, dentro de los umbrales del sensor, así que no abre alertas. El servicio de lecturas no actualiza `last_seen_at` ni resuelve alertas, así que la lectura no tiene más efectos.

**Las credenciales salen de `.env`.** El script lo carga con `. ./.env` para usar `POSTGRES_USER`, `POSTGRES_DB` y `SIMULATOR_SCENARIO`, igual que hace Compose.

**El seed no lo ejecuta el smoke test.** Si falta el sensor, falla con `make seed` como instrucción. Así el smoke test no modifica datos de nadie salvo su propia lectura, que borra al terminar.

## 4. Criterios de aceptación

Los siete puntos de la sección 8 de `01-issue.md`:

| Criterio | Comprobación | Resultado |
|---|---|---|
| Database reporta readiness | healthcheck `pg_isready` | `database` en `healthy` |
| Backend reporta readiness según sus dependencias | `/api/health/db` | responde con la base arriba |
| Compose muestra estados saludables | `docker compose up --wait` | `Healthy` en los tres servicios |
| El smoke test espera readiness con timeout | `--wait-timeout 60` | con la base congelada falla al agotar el tiempo |
| Una lectura válida devuelve respuesta exitosa | `POST /api/readings` | 201 |
| Se comprueba su persistencia | `SELECT count(*) FROM readings WHERE id = ...` | 1 |
| Cualquier fallo termina con código distinto de cero y diagnóstico | base congelada, seed sin cargar | código 1 y mensaje con los logs a revisar |

Y los tres de la issue de GitHub:

| Criterio | Resultado |
|---|---|
| Backend y database reportan estado saludable | sí, por healthcheck y por `/api/health/db` |
| El smoke test detecta fallos básicos | sí, ver punto 5 |
| El flujo simulator → API funciona en Docker | sí, con `make sim` el smoke ve lecturas del simulador en la base |

## 5. Verificación

**Stack sano, sin simulador.**

```text
$ make smoke
smoke: waiting up to 60s for database, backend and gateway...
 Container ft_transcendence-database-1  Healthy
 Container ft_transcendence-backend-1  Healthy
 Container ft_transcendence-gateway-1  Healthy
smoke: ok    database, backend and gateway are healthy
smoke: ok    /api/health responds
smoke: ok    /api/health/db responds
smoke: ok    HTTP redirects to HTTPS
smoke: ok    the gateway serves the SPA
smoke: ok    POST /api/readings accepts a reading
smoke: ok    the reading is stored in PostgreSQL
smoke: skip  simulator is not running (make sim)
smoke: OK, all checks passed
```

Después, en la base no queda ninguna lectura de 3,5 bar del sensor `SENS-001`: la de prueba se borró.

**Con el simulador recién arrancado.**

```text
$ make sim && make smoke
...
smoke: ok    simulator readings reach the database (6 in the last 30s)
smoke: OK, all checks passed
```

**Simulador en escenario `offline`.** El simulador sigue `healthy`, porque su heartbeat se actualiza aunque no envíe nada, pero no llega ninguna lectura. Sin tratarlo aparte, el smoke fallaría en un escenario válido:

```text
smoke: skip  simulator scenario is offline, it sends no readings on purpose
smoke: OK, all checks passed
```

**Sin seed.** Con un sensor que no existe:

```text
smoke: FAIL  the demo sensor does not exist. Load the demo data with: make seed
```

**Servicio que no se pone sano.** `docker compose pause database` congela la base: el contenedor existe pero no responde, y Compose no puede reiniciarlo.

```text
$ docker compose pause database
$ make smoke
smoke: waiting up to 60s for database, backend and gateway...
Error response from daemon: cannot start a paused container, try unpause instead
smoke: FAIL  the stack is not healthy. Check it with: docker compose ps
```

**Servicio parado.** Con `docker compose stop backend`, el smoke no falla: `up --wait` vuelve a arrancar el backend, espera a que esté sano y sigue. Si el backend no consiguiera arrancar, por ejemplo por un error en el código, no llegaría a `healthy` y `--wait` fallaría como en el caso anterior.

En todos los fallos el código de salida es 1 y `make` lo propaga.

## 6. Errores frecuentes descartados

Los cinco de `04-implementacion.md`:

* **Confundir `running` con `healthy`.** `docker compose up --wait` espera al estado del healthcheck, no al del contenedor.
* **Sleeps largos en lugar de readiness.** El script no tiene ningún `sleep`: la espera la hace Compose, con un límite de 60 segundos.
* **Comprobar solo un 200 sin verificar persistencia.** Además de la respuesta del `POST`, busca la lectura en PostgreSQL por su `id`.
* **Datos fijos que chocan al repetir el test.** UUID nuevo en cada ejecución, y la lectura se borra al final.
* **Ocultar excepciones y devolver siempre éxito.** Cada comprobación sale con `exit 1` si falla, y el `OK` final solo se imprime si pasan todas.

## 7. Pendiente conocido

* **El smoke test no corre en CI.** `.github/workflows/` sigue sin `ci.yml`. Es la #94, que pide justo `scripts/smoke.sh` y `make smoke`: este script ya cumple esa parte y la #94 puede reutilizarlo.
* **`scripts/wait_for_stack.sh`**, que la #94 menciona como dependencia, no existe: es de la #90 (Daruny). Aquí no hace falta, porque `docker compose up --wait` hace esa espera.
* **Si la lectura de prueba se guarda pero un paso posterior falla**, por ejemplo al buscarla en PostgreSQL, la lectura no se borra. Es una lectura normal de 3,5 bar y no afecta a la demo.
* **La comprobación del simulador mira las lecturas de los últimos 30 segundos de cualquier sensor**, no de cada uno. Basta con que llegue una.
* **El simulador arranca con `depends_on: backend: condition: service_started`**, no `service_healthy`. No es un problema porque el simulador espera a `/api/health/db` por su cuenta antes de enviar, pero se podría alinear con el gateway.
