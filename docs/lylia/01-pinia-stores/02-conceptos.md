# Conceptos — Issue 01

## Modelo mental

Un store es un estado reactivo compartido y una interfaz de acciones. El componente lo consume y renderiza; el service obtiene datos; el store coordina estado, no markup.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Reactividad | Cambios de estado actualizan consumidores | 25 min |
| Store | Fuente compartida por dominio | 25 min |
| State | Datos mutables observables | 15 min |
| Getter | Valor derivado sin efectos secundarios | 20 min |
| Action | Operación que cambia/recarga estado | 25 min |
| Estado remoto | Idle/loading/data/error | 25 min |
| Persistencia | Qué sobrevive a un refresh | 25 min |
| Inmutabilidad práctica | Evitar mutaciones inesperadas | 20 min |

## Conceptos en conjunto

Pinia no es una base de datos ni un cliente HTTP. Una action puede llamar un service y actualizar `loading/data/error`, pero la vista no debe saber cómo se construyó la request. Los getters derivan información y no deben producir efectos.

Auth Store identifica sesión/usuario; Sensors Store conserva colección/selección; Alerts Store conserva alertas/filtros. Separar dominios evita un store gigante.

## Qué debes poder demostrar

- Explicar quién cambia cada propiedad.
- Consumir un getter desde una vista.
- Reiniciar estado en logout.
- Representar error sin dejar `loading=true` para siempre.

## Errores frecuentes

Guardar estado duplicado, llamar API desde getters, meter referencias DOM en stores, mezclar filtros locales con datos globales y no limpiar auth al cerrar sesión.
