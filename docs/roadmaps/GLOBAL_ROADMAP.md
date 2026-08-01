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

## Open

| # | Item | Severity |
| :--- | :--- | :--- |
| F-008 | `dependabot.yml` declares no grouping and no `open-pull-requests-limit`. With Dependabot now enabled at the repository level, a routine week can open one pull request per package. | Low |
| R-001 | `docs/guides/CORE_DEPLOYMENT_GUIDE.md` predates the `/health/` endpoint and the `CACHES` block; neither is documented as a deployment concern. | Low |
| R-002 | The `users` identity app (`User-APP-Template`) will need a shared cache for TOTP anti-replay and step-up authentication. This template deliberately defaults to `LocMemCache` — the installing app must assert the requirement itself, and that contract is not yet written down anywhere but ADR-0001's neighbourhood. | Medium, blocks the `users` install |
| **I-001** | **Brute-force protection degrades to per-IP when a custom `AUTH_USER_MODEL` is installed.** Found by the P5 integration run: with `users.User` (`USERNAME_FIELD = 'email'`) installed, failed logins through `/admin/login/` are recorded by `django-axes` with `username=None`. Lockout then keys on `(None, ip_address)`, so every account behind one IP shares a bucket, and `AXES_RESET_ON_SUCCESS` never matches — the counter does not clear after a correct login. Verified: `AccessAttempt.objects.values()` returns `{'username': None, 'failures_since_start': 3}` before and after a successful login. The same app's own `/me/reauth/` path records the username correctly, so the defect is specific to the admin form path. Root cause not yet established; do not guess a fix. | **High**, blocks the users install |
| R-003 | C4 Level 3 stays advisory while `backend/apps/` holds a single container. It becomes required as soon as a second app is installed. | Informational |

## Deferred by design

- `models.py` and `admin.py` in `apps.core` remain stubs. This is a template; the first domain app is the consumer's decision, not a gap.
- No `AUTH_USER_MODEL` is set. Swapping in a custom user model is a decision each fork makes for itself.

---
*Updated at every Sprint Closeout (RA-05).*
