# Conceptos — Issue 05

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Hash | Transformación no reversible para password | 25 min |
| Salt | Evita hashes iguales para passwords iguales | 15 min |
| Verificación | Comparar password sin recuperar el original | 20 min |
| Sesión | Estado que identifica al usuario | 25 min |
| Cookie segura | Transporte con flags HttpOnly/Secure/SameSite | 30 min |
| Bearer token | Credencial enviada en Authorization | 25 min |
| Expiración/revocación | Limitar vida y cortar acceso | 25 min |
| 401 vs 403 | No autenticado frente a no autorizado | 15 min |

## Conceptos relacionados

Autenticación responde “¿quién eres?”; autorización responde “¿qué puedes hacer?”. Esta issue identifica al usuario; la 06 aplica organización y rol. El hash protege una password almacenada, pero no sustituye una sesión segura.

El mecanismo elegido debe coincidir con frontend, gateway y decisión documentada en `docs/decisions/0001-auth-cookie.md`.

## Errores frecuentes

Guardar passwords, comparar hashes manualmente, devolver “email no existe”, usar cookies sin flags o aceptar un token expirado.
