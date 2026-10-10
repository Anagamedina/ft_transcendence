# Conceptos — Issue 07

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Loading | Trabajo en curso y prevención de acciones duplicadas | 20 min |
| Empty | Resultado correcto sin elementos | 15 min |
| Error | Fallo recuperable o no | 20 min |
| Retry | Repetir operación con feedback | 20 min |
| State machine | Transiciones sin estados contradictorios | 25 min |
| Skeleton/spinner | Feedback visual apropiado | 20 min |
| Live region/focus | Comunicar cambios accesiblemente | 25 min |

## Conceptos en conjunto

Una vista remota no tiene solo “datos o error”. Puede estar cargando, vacía, parcial o fallida. El store determina el estado; estos componentes lo presentan y emiten retry.

## Errores frecuentes

Mostrar spinner infinito, usar Empty ante error, perder el mensaje al reintentar, botón retry sin foco y duplicar estados dentro de cada vista.

## Qué debes dominar antes de implementar

- Modelar estados sin combinaciones contradictorias.
- Definir quién cambia el estado y quién solo lo presenta.
- Hacer retry sin duplicar requests ni perder foco.
- Diferenciar cero, vacío, carga y error.

## Qué debes poder demostrar

- Diferenciar ready, empty y error.
- Mantener foco y mensaje después de retry.
- Integrar el mismo componente en varias vistas.
