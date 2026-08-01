# 📄 Contract: CORE
**File**: `docs/contracts/CORE_CONTRACT.md` (RA-06 Option B naming)
**Module**: CORE
**Last Audit Sprint**: #001
**Last Audit Date**: 2026-08-01

---

Formal interfaces `apps.core` exposes. Reference material: shapes and status codes, no rationale. The reasoning behind each lives in the ADRs linked from `docs/architecture/CORE_BLUEPRINT.md`.

## `GET /health/`

Liveness and readiness probe. Unauthenticated — an orchestrator polling it has no session, and a probe that needs credentials is a probe that fails during exactly the incident it exists to detect.

**Request**: no parameters, no body. Any method other than `GET` returns `405`.

**Response**: `application/json`

| Field | Type | Values |
| :--- | :--- | :--- |
| `database` | string | `"OK"` \| `"DOWN"` |
| `cache` | string | `"OK"` \| `"DOWN"` |
| `system` | string | `"HEALTHY"` \| `"DEGRADED"` |

| Status | Meaning |
| :--- | :--- |
| `200` | Every dependency responded. `system` is `"HEALTHY"`. |
| `503` | At least one dependency failed. `system` is `"DEGRADED"`, and the failing key reads `"DOWN"`. |
| `405` | Method other than `GET`. |

Each dependency is probed independently, so one failure never masks the state of the other.

```json
{"database": "OK", "cache": "DOWN", "system": "DEGRADED"}
```

**Note for operators**: the endpoint reports which subsystem is degraded, which is mild reconnaissance value to an unauthenticated caller. Restrict it at the ingress if that matters in your deployment.

## `PasswordComplexityValidator`

Django validator protocol, registered in `AUTH_PASSWORD_VALIDATORS`.

**`validate(password: str, user=None) -> None`** — returns nothing on success; raises `django.core.exceptions.ValidationError` on the first rule that fails.

| Rule | Error `code` |
| :--- | :--- |
| At least one uppercase letter | `password_no_upper` |
| At least one lowercase letter | `password_no_lower` |
| At least one digit | `password_no_digit` |
| At least one non-alphanumeric character, `_` included | `password_no_symbol` |

Codes are stable: a client localises its messages from them rather than parsing English strings.

**`get_help_text() -> str`** — the requirement summary Django renders in forms.

## `core.E001` / `core.W001`

Django system check, registered under `Tags.admin`. Constructs every registered `ModelAdmin` form and `InlineModelAdmin` formset.

| ID | Level | Raised when |
| :--- | :--- | :--- |
| `core.E001` | Error | A `FieldError` — a declared field does not exist on the bound model |
| `core.W001` | Warning | Any other construction failure, which may be an artefact of the check's request stub rather than a real defect |

Runs on `manage.py check`. Django's own admin checks do not validate inline `fields`, so without this a misconfigured inline reaches production as a 500 on the change page.
