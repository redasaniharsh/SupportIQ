"""Security placeholder.

No auth/RBAC is implemented in this base build (documented trade-off in
DESIGN.md section 12 — out of scope for the assessment time budget).

Future improvement: add JWT-based auth (e.g. via OAuth2PasswordBearer +
python-jose), per-role permissions for agents vs admins, and API-key auth
for service-to-service calls (ingestion scripts hitting the API instead of
writing to Mongo directly). Any such implementation must keep secrets out
of source control and reuse app.core.config.Settings for configuration.
"""
from __future__ import annotations


def get_current_user_placeholder() -> dict:
    """Placeholder dependency for a future auth system.

    Currently returns a static anonymous "system" identity so that fields
    like `resolved_by` / `assignee_id` can still be captured from request
    bodies rather than from a real authenticated session.
    """
    return {"id": "anonymous", "role": "agent"}
