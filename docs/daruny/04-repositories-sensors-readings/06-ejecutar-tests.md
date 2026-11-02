# Ejecutar tests — Issue 04

Pasos para correr `test_sensor_reading_repositories.py` en local.

1. `cd backend`
2. `python3 -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `pip install pytest` (no está en `requirements.txt`)
6. `pytest tests/unit/test_sensor_reading_repositories.py -v`
7. `deactivate` (al terminar)

## Resultado esperado

```
4 passed
```

Si algún test falla de forma intermitente (pasa unas veces y otras no), es señal de un `order_by` no determinista en el repository — no de un problema del entorno.
