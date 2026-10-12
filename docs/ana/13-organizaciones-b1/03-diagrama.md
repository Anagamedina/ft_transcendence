# Diagrama — Issue 13 (B1)

## Estados de una organización

```mermaid
stateDiagram-v2
  [*] --> ACTIVE: POST /organizations (admin)
  [*] --> TRIAL: registro público (B10)
  TRIAL --> TRIAL: extend-trial (+TRIAL_DAYS)
  TRIAL --> ACTIVE: activate (borra trial_ends_at)
  ACTIVE --> SUSPENDED: suspend
  TRIAL --> SUSPENDED: suspend
  SUSPENDED --> TRIAL: reactivate, si tiene trial_ends_at
  SUSPENDED --> ACTIVE: reactivate, si no
```

Cualquier otra transición → **409** (`ORGANIZATION_ALREADY_SUSPENDED`,
`ORGANIZATION_NOT_SUSPENDED`, `ORGANIZATION_NOT_IN_TRIAL`).

## Suspender deja fuera a los usuarios

```mermaid
sequenceDiagram
  participant C as Cliente (sesión abierta)
  participant A as Admin
  participant API
  A->>API: POST /organizations/{id}/suspend
  API-->>A: 200 status=SUSPENDED
  C->>API: GET /api/me (cookie válida)
  API->>API: get_current_user → ensure_account_enabled
  API-->>C: 403 ACCOUNT_DISABLED
```

## Contadores sin N+1

```mermaid
flowchart LR
  L["list(): 20 organizaciones"] --> C["counts(ids)"]
  C --> Q1["GROUP BY sites"]
  C --> Q2["GROUP BY sensores"]
  C --> Q3["GROUP BY usuarios"]
  C --> Q4["GROUP BY alertas ACTIVE × severidad"]
  Q1 & Q2 & Q3 & Q4 --> R["OrganizationResponse × 20"]
```
