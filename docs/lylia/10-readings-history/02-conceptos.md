# Conceptos — Issue 10

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Serie temporal | Valores asociados a momentos | 25 min |
| Orden temporal | Orden estable y zona horaria | 25 min |
| Sampling | Densidad de puntos mostrados | 20 min |
| Rango | Ventana temporal consultada | 20 min |
| Selection state | Sensor activo y su histórico | 20 min |
| Chart boundary | Preparar datos sin acoplar librería | 25 min |

## Conceptos en conjunto

Backend limita/ordena datos; service los obtiene; store conserva selección; componente presenta. El frontend no debe inventar timestamps ni asumir que todos los sensores tienen readings.

## Errores frecuentes

Mezclar históricos al cambiar sensor, ordenar strings de fecha incorrectamente, ignorar zona horaria, cargar cantidades ilimitadas y acoplar el store a Chart.js.

## Qué debes dominar antes de implementar

- Explicar cómo se identifica la serie activa.
- Verificar orden, zona horaria y límites.
- Evitar mostrar datos de un sensor anterior.
- Separar mapper de datos y librería de gráficas.

## Qué debes poder demostrar

- Explicar cómo se identifica la serie activa.
- Verificar orden y zona horaria.
- Mostrar vacío sin confundirlo con error.
