# 🗺️ Global Roadmap: Django Pro Template
**Last Audit Sprint**: #001
**Last Audit Date**: 2026-08-01

---

Backlog derived from `docs/audits/AUDIT_001_BACKEND.md`. Every item traces to a verified finding — nothing here is speculative.

## ✅ Closed in Sprint #001

| # | Item |
| :--- | :--- |
| F-001 | Application loggers reach a handler (`apps`, `config`, `utils` prefixes registered) |
| F-002 | Optional boolean keys fall back to their default when interpolated empty |
| F-003 | `.env` loads for every entrypoint, not only `manage.py` |
| F-004 | `/health/` endpoint probing database and cache independently |
| F-005 | Explicit `CACHES` block with optional Redis |
| F-006 | `.gitignore` covers the log directory the application actually creates |
| F-007 | Workflows declare `permissions: contents: read` |
| — | pytest harness, Django 6.0.7, four retroactive ADRs, reusable CI workflow |
| R-002 | The shared-cache requirement is now asserted by the installing app rather than assumed here: `django-users-app` states it under *Host requirements* in its `USERS_CONTRACT.md`, which is where a consumer looks. This template keeps its `LocMemCache` default deliberately |
| I-001 | `AXES_USERNAME_FORM_FIELD` pinned to `'username'`. Raised by the integration run: install a user model keyed on email and axes 8 records every `/admin/login/` failure as `username=None`, degrading lockout from per-account to per-IP while `AXES_RESET_ON_SUCCESS` stops matching — silently, with nothing raised. Root cause is an axes default that changed between 6.5.1 (literal `"username"`) and 8.3.1 (derived from `USERNAME_FIELD`), both read from the installed packages. Guarded by `AxesLockoutTest.test_username_form_field_is_pinned_rather_than_derived`, checked to fail without the pin |

## Open

| # | Item | Severity |
| :--- | :--- | :--- |
| F-008 | `dependabot.yml` declares no grouping and no `open-pull-requests-limit`. With Dependabot now enabled at the repository level, a routine week can open one pull request per package. | Low |
| R-001 | `docs/guides/CORE_DEPLOYMENT_GUIDE.md` predates the `/health/` endpoint and the `CACHES` block; neither is documented as a deployment concern. | Low |
| R-003 | C4 Level 3 stays advisory while `backend/apps/` holds a single container. It becomes required as soon as a second app is installed. | Informational |

## Deferred by design

- `models.py` and `admin.py` in `apps.core` remain stubs. This is a template; the first domain app is the consumer's decision, not a gap.
- No `AUTH_USER_MODEL` is set. Swapping in a custom user model is a decision each fork makes for itself.

---
*Updated at every Sprint Closeout (RA-05).*
