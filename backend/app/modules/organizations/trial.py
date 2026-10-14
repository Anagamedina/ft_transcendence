# TRIAL — organizations
# Regla que decide si la prueba de una organización ha vencido (B12).
# Sin base de datos.
"""
Prueba vencida (B12, issue #146).

Una organización tiene la prueba **vencida** si está en `TRIAL` y su
`trial_ends_at` ya ha pasado. Con la prueba vencida la cuenta queda en
solo lectura (`require_trial_not_expired` en `shared/dependencies.py`).

- **Vence en el instante exacto de `trial_ends_at`**, el mismo criterio
  que usa `extend-trial` para decidir si cuenta desde el fin o desde hoy.
- **Se calcula, no se guarda.** No hay tarea periódica que pase la
  organización a otro estado: ampliar o activar la prueba (B1) basta para
  que deje de estar vencida.
- Una `SUSPENDED` que estaba en prueba conserva `trial_ends_at`, pero no
  cuenta como vencida: a esa la corta `ACCOUNT_DISABLED` antes.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.organizations.model import Organization
from app.shared.enums import OrganizationStatus


def trial_expired(
    organization: Organization | None, ahora: datetime | None = None
) -> bool:
    """
    `ahora` se puede pasar desde fuera para probarlo sin depender del reloj.
    """
    if organization is None or organization.status != OrganizationStatus.TRIAL.value:
        return False
    fin = organization.trial_ends_at
    if fin is None:
        return False
    # sqlite (tests) devuelve la fecha sin zona; se guarda en UTC.
    if fin.tzinfo is None:
        fin = fin.replace(tzinfo=timezone.utc)
    return fin <= (ahora or datetime.now(timezone.utc))
