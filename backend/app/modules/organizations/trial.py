# TRIAL — organizations
# Rule that decides whether an organization's trial has expired (B12).
# No database.
"""
Expired trial (B12, issue #146).

An organization's trial is **expired** if it is in `TRIAL` and its
`trial_ends_at` has passed. With the trial expired the account becomes
read-only (`require_trial_not_expired` in `shared/dependencies.py`).

- **It expires at the exact instant of `trial_ends_at`**, the same rule
  `extend-trial` uses to decide whether to count from the end or from
  today.
- **It is computed, not stored.** No periodic task moves the organization
  to another status: extending the trial (B1) or becoming a client (B14)
  is enough for it to stop being expired.
- A `SUSPENDED` organization that was on trial keeps `trial_ends_at`, but
  does not count as expired: `ACCOUNT_DISABLED` stops it first.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.organizations.model import Organization
from app.shared.enums import OrganizationStatus


def trial_expired(
    organization: Organization | None, ahora: datetime | None = None
) -> bool:
    """
    `ahora` ("now") can be passed in to test it without depending on the
    clock.
    """
    if organization is None or organization.status != OrganizationStatus.TRIAL.value:
        return False
    fin = organization.trial_ends_at
    if fin is None:
        return False
    # sqlite (tests) returns the date without a zone; it is stored in UTC.
    if fin.tzinfo is None:
        fin = fin.replace(tzinfo=timezone.utc)
    return fin <= (ahora or datetime.now(timezone.utc))
