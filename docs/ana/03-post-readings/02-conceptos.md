# Conceptos — Issue 03 (#24)

## Modelo mental

`POST /api/readings` es **el único punto por el que entra un dato al
sistema**. Todo lo que el producto muestra —gráficas, KPIs, alertas—
depende de lo que se guarde aquí. Por eso esta issue, que parece un
endpoint sencillo, concentra las decisiones que más caro cuesta cambiar.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| El flujo vertical | Por qué es la primera funcionalidad obligatoria | 20 min |
| Idempotencia y 201 | Qué código devolver al crear | 15 min |
| `measured_at` vs `created_at` | Dos tiempos distintos, no uno duplicado | 30 min |
| Zonas horarias | *Naive* frente a *aware*, y por qué rompe | 25 min |
| Efectos secundarios | `last_seen_at` y por qué se actualiza aquí | 20 min |
| Excepciones que suben | Por qué el router no lleva `try/except` | 20 min |

---

## 1. El flujo vertical

```
Simulator → POST /api/readings → FastAPI → Service → Repository → PostgreSQL
```

El documento (apartado 8.5) marca esto como primera funcionalidad
obligatoria y añade: *hasta que este flujo funcione correctamente, no se
priorizan funcionalidades más complejas*.

La razón es que atraviesa **todas** las capas del sistema. Cuando
funciona, están probados el contrato, la validación, la inyección de
dependencias, la sesión de base de datos y la persistencia. Cualquier
funcionalidad posterior es una variación de ese camino.

### Quién llama a quién

El simulador vive dentro de la red de Docker Compose y llama a
`backend:8000` **por el nombre de servicio**. No pasa por Nginx.

Consecuencia práctica muy útil: **se puede probar este endpoint sin Nginx
y sin certificados**. Solo el tráfico del navegador atraviesa el gateway.

---

## 2. Los dos tiempos de una lectura

El concepto central de esta issue.

```
measured_at → cuándo el sensor tomó la medida
created_at  → cuándo el backend la registró
```

Con el simulador en la misma red se diferencian en milisegundos, y por eso
parece que uno sobra. Con sensores reales no:

> Una pasarela sin cobertura acumula lecturas y las envía media hora
> después. Si solo guardas el instante de inserción, la gráfica dibuja
> todas esas lecturas **apiladas en el momento en que llegaron**, no
> cuando ocurrieron. El pico de presión aparece a la hora equivocada.

Que la regla 5.1 del documento pida un índice por `(sensor_id,
measured_at)` lo confirma: la ordenación del histórico va por
`measured_at`.

`measured_at` es **opcional en la entrada**: si no llega, el servidor usa
el momento de recepción.

---

## 3. Zonas horarias: *naive* frente a *aware*

```python
datetime(2026, 8, 21, 9, 15)                      # naive  — ¿9:15 dónde?
datetime(2026, 8, 21, 9, 15, tzinfo=timezone.utc) # aware  — 9:15 UTC
```

Comparar un *naive* con un *aware* lanza `TypeError` en tiempo de
ejecución. En un histórico eso significa lecturas ordenadas al azar o un
500 al pintar la gráfica.

La norma del proyecto: **todo se normaliza a UTC en la frontera**.

```python
if value.tzinfo is None:
    return value.replace(tzinfo=timezone.utc)
return value.astimezone(timezone.utc)
```

Y hacia fuera, ISO-8601 terminado en `Z`: `"2026-08-21T09:15:00Z"`.

---

## 4. Crear tiene efectos secundarios

Registrar una lectura no es solo un `INSERT`. Son seis pasos:

```
1. ¿existe el sensor?          → si no, 404 SENSOR_NOT_FOUND
2. resolver measured_at
3. guardar la lectura
4. actualizar last_seen_at del sensor
5. evaluar umbrales → ¿alerta?          (issue #28)
6. devolver la fila creada
```

**El paso 1** evita lecturas huérfanas: una `sensor_id` inventada crearía
filas que no aparecen en ningún histórico.

**El paso 4** es el que más se olvida. `SENSOR_OFFLINE` se detecta por lo
que **deja** de llegar, no por lo que llega. Sin `last_seen_at`
actualizado no hay forma de saber que un sensor lleva dos horas mudo,
porque no hay ninguna lectura en la que apoyarse.

**El paso 5** distingue esta issue de la #28: aquí se deja el hueco, allí
se implementa la regla.

---

## 5. Por qué 201 y no 200

Se ha creado un recurso. El simulador comprueba exactamente eso:

```python
if r.status_code != 201:
    print("rechazada:", r.status_code, r.json())
```

Y por eso el error lleva un `code` estable: al simulador le sirve para
distinguir «dato malo» (no reintentar) de «servidor caído» (reintentar).

---

## 6. Las excepciones suben solas

```
service.py   raise NotFoundError("Sensor no encontrado",
                                 code="SENSOR_NOT_FOUND")
    ↑ sube
router.py    no la atrapa — no hay try/except
    ↑ sube
handler      lee exc.status_code y exc.code, construye el envelope
    ↓
cliente      404  {"error": {"code": "SENSOR_NOT_FOUND", ...}}
```

Poner un `try/except` en el router para convertirla en un 404 duplicaría
en cada endpoint lo que ya hace un único handler — y en cuanto uno se
olvide, ese endpoint devolverá un 500 en lugar de un 404.

---

## 7. Qué va en cada archivo

| | **SÍ** | **NUNCA** |
|---|---|---|
| `router.py` | Decorador con `status_code`, `response_model` y `responses`; parámetros tipados; `Depends`; una línea que delega | `session.query(...)`; `if` de negocio; `try/except` para códigos HTTP |
| `service.py` | Reglas: existe, está en rango, quién tiene permiso; coordinar repositories; lanzar `NotFoundError`; convertir a schema | `HTTPException`, `status_code`, `Request`; `select()`, `commit()`; saber si vino del simulador o del navegador |

---

## Errores frecuentes

- Guardar solo un timestamp y descubrirlo cuando la gráfica sale mal.
- Olvidar `last_seen_at` y quedarse sin `SENSOR_OFFLINE`.
- Rechazar como inválida una presión anómala (que es la que interesa).
- Aceptar `sensor_id` sin comprobar que existe.
- Devolver 200 en lugar de 201 y romper la comprobación del simulador.

---

## Qué debes poder demostrar

- Recorrer el flujo vertical entero nombrando qué archivo hace qué.
- Explicar por qué hacen falta `measured_at` **y** `created_at`.
- Decir qué pasa si no se actualiza `last_seen_at`.
- Justificar por qué 0–25 bar se rechaza pero fuera de umbral se guarda.
- Explicar cómo llega un `NotFoundError` del service al JSON del cliente
  sin que el router lo toque.
