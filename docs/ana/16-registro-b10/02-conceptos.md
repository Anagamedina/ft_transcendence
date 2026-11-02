# Conceptos — Issue 16 (B10)

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Registro que abre sesión | El router pone la misma cookie que el login: quien se registra ya está dentro | 10 min |
| Una transacción para dos filas | Organización y usuario se guardan juntos: si falla el usuario, no queda una organización vacía | 15 min |
| Comprobar y luego guardar no basta | Dos registros a la vez pasan los dos la comprobación; el índice único para al segundo, y el `IntegrityError` se traduce al 409 | 20 min |
| Regla de contraseñas en el service | Para que el error tenga su código (`WEAK_PASSWORD`) y para que el login no la herede | 15 min |
| Enumeración de cuentas | El 409 `EMAIL_ALREADY_EXISTS` dice que un email existe; el login lo evita, el registro lo acepta y lo frena el límite de Nginx (I1) | 15 min |

## Conceptos relacionados

El login tiene cuidado de no revelar qué emails existen (mismo mensaje y
mismo tiempo). El registro no puede hacer lo mismo sin dejar al usuario
sin saber por qué no se registra, así que avisa con un 409. Es una
decisión consciente: lo que impide probar miles de emails es el límite de
peticiones de Nginx.

La longitud máxima (128) no es por seguridad: Argon2 tarda más cuanto más
larga es la contraseña, y sin tope una contraseña de un mega dejaría el
servidor ocupado.

## Qué debes poder demostrar

- Contar qué se guarda en una sola transacción y por qué.
- Explicar por qué `e2e-password` vale (12 caracteres, variados) y `password1234` no.
- Explicar por qué el login sigue aceptando contraseñas viejas de 8 caracteres.
