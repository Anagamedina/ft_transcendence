# Diagrama — Issue 05

```mermaid
sequenceDiagram
 participant U as Usuario
 participant V as Formulario
 participant S as AuthService
 participant A as AuthStore
 participant B as Backend
 U->>V: email/password
 V->>S: login(payload)
 S->>B: POST /auth/login
 B-->>S: cookie/token + user
 S->>A: setSession(user)
 A-->>U: zona privada
 U->>S: logout()
 S->>B: POST /auth/logout
S->>A: reset()
```

La credencial se transporta según la decisión del proyecto; la UI no debe inventar una segunda estrategia.

Antes: formularios aislados. Después: sesión compartida y navegable.
