# 🏛️ Blueprint: CORE
**File**: `docs/architecture/CORE_BLUEPRINT.md` (RA-06 Option B naming)
**Status**: `RATIFIED`
**Sprint of origin**: #000 (Legacy Onboarding — Full Reverse Engineering, Scenario C)
**Last Audit Sprint**: #000 (Security Hardening + Containerized Deploy — Rounds 1-4)
**Last Audit Date**: 2026-07-28
**Last Audit Commit SHA**: f5ea84d365697d67dda090cae53d935e68eb3b29

---

arc42-lite (`rules/documentation_standard.md §5`) — Reference only. This document states current facts, verifiably; it never argues for them. Any decision behind this module's shape lives in a linked ADR, not here.

## 1. Introduction & Goals
`apps.core` (`backend/apps/core/`) is the sole local Django app installed in this project. Today it holds no domain models or views of its own — `models.py`, `views.py`, and `admin.py` are all unmodified Django stubs. Its one piece of real logic is `PasswordComplexityValidator`, wired into Django's `AUTH_PASSWORD_VALIDATORS` at project level. It is the designated landing place for future domain apps to be split out of, not a feature module itself yet. The bulk of this project's actual security posture lives in `backend/config/settings.py` (project-level, not owned by `core`) — CSP, CORS/CSRF, brute-force lockout, permissions policy — which `core`'s test suite exercises functionally (see §6).

## 2. Context & Scope
| Aspect | Value |
| :--- | :--- |
| **Upstream dependencies** | `backend/config/settings.py` (registers the app in `INSTALLED_APPS` and references `apps.core.validators.PasswordComplexityValidator`); third-party security middleware stack it runs alongside: `corsheaders`, `csp`, `axes`, `django_permissions_policy`, `whitenoise`; runtime container defined by the repo-root `Dockerfile` (gunicorn + `docker-entrypoint.sh`) |
| **Downstream consumers** | Django's auth framework (via `AUTH_PASSWORD_VALIDATORS`); `backend/config/urls.py` does not yet route to any `apps.core` view |

## 3. Building Block View
| Aspect | Value |
| :--- | :--- |
| **Owns** | `backend/apps/core/` (`apps.py`, `models.py`, `views.py`, `admin.py`, `validators.py`, `tests.py`) |
| **Must not touch** | `backend/config/` (project-level settings/URL root — owned by the Django project itself, not by `core`) |

Contracts (formal interfaces this module exposes):

| Interface | Type | Defined in |
| :--- | :--- | :--- |
| `PasswordComplexityValidator.validate(password, user=None)` | Python class, Django validator protocol | `backend/apps/core/validators.py` |

Data model (summary only — key entities and relations, one line each; full schemas belong in the contract):
- None today — `models.py` is an unmodified stub (`# Create your models here.`).

## 4. Runtime View
1. During any password set/change flow (Django admin, `createsuperuser`, future auth views), Django's password-validation pipeline invokes `PasswordComplexityValidator.validate()` in the order declared in `AUTH_PASSWORD_VALIDATORS` (`backend/config/settings.py`), after the built-in similarity/length/common/numeric validators and before `PwnedPasswordsValidator`.
2. The validator checks, via regex, for at least one uppercase letter, one lowercase letter, one digit, and one non-alphanumeric character (including `_`), raising `django.core.exceptions.ValidationError` with a specific `code` (`password_no_upper`, `password_no_lower`, `password_no_digit`, `password_no_symbol`) on the first rule it fails.

## 5. Crosscutting Concepts
- **Fail-fast configuration**: the project-level `settings.py` raises `ImproperlyConfigured` at import time if required config (`DJANGO_SECRET_KEY`, DB components, production `ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`, production email settings) is missing, or if a security-relevant boolean (`DEBUG`, `EMAIL_USE_TLS`, `TRUST_PROXY_SSL_HEADER`, `CROSS_SITE_FRONTEND`) isn't exactly `"true"`/`"false"` (case-insensitive) — via the shared `_parse_strict_bool` helper. `apps.core` inherits this posture but does not itself implement config loading.
- **Password hardening stack**: `core`'s validator is one layer in a five-validator chain (`AUTH_PASSWORD_VALIDATORS`) that also includes `pwned_passwords_django`, giving both structural (complexity) and breach-database (pwned) checks.
- **Cross-origin session auth**: `CORS_ALLOWED_ORIGINS` doubles as `CSRF_TRUSTED_ORIGINS` and enables `CORS_ALLOW_CREDENTIALS`, so a decoupled frontend at those origins can authenticate by session cookie. For a frontend on a genuinely different registrable domain (not just a different port/subdomain), the opt-in `CROSS_SITE_FRONTEND` flag additionally sets `SESSION_COOKIE_SAMESITE`/`CSRF_COOKIE_SAMESITE` to `'None'` — browsers never send `SameSite=Lax` (the default) cookies on cross-site `fetch`/`XHR`.
- **Brute-force login protection**: `django-axes` locks out a `(username, ip_address)` pair for `AXES_COOLOFF_TIME` after `AXES_FAILURE_LIMIT` failed attempts (HTTP 429), resetting the count on a successful login (`AXES_RESET_ON_SUCCESS`). Covers `/admin/login/` and any future auth view via `AxesStandaloneBackend`.
- **Response security headers**: `django-csp` (`CONTENT_SECURITY_POLICY`, 4.0+ dict format) and `django-permissions-policy` (`PERMISSIONS_POLICY`, list-of-origins-per-feature format) both apply only in the `if not DEBUG:` block — verified empirically not to break the Django admin UI (no inline `<script>`/`style=` in its rendered pages).
- **Reverse-proxy TLS trust**: `SECURE_PROXY_SSL_HEADER` is opt-in only (`TRUST_PROXY_SSL_HEADER`), never enabled by default, since trusting `X-Forwarded-Proto` blindly lets a client spoof it when there's no proxy actually stripping that header.
- **Static file serving**: `whitenoise` (`WhiteNoiseMiddleware`, directly after `SecurityMiddleware`; `STORAGES['staticfiles']` set to its compressed-manifest backend) serves collected static files directly from the app process — no separate proxy/CDN required for a generic deploy. See `docs/DEPLOYMENT.md`.
- **Container startup order**: `docker-entrypoint.sh` runs `migrate --noinput` then `collectstatic --noinput` on every container start (not at build time, since both need real env vars/DB connectivity that don't exist yet during `docker build`) before `exec`-ing into gunicorn — see `docs/DEPLOYMENT.md` for the multi-replica caveat on automatic `migrate`.

## 6. Non-negotiable Constraints
| Constraint | Verification |
| :--- | :--- |
| `PasswordComplexityValidator` must run before `PwnedPasswordsValidator` is bypassed by a structurally-valid-but-breached password | Order in `AUTH_PASSWORD_VALIDATORS`, `backend/config/settings.py` |
| `apps.core` must not introduce a competing settings/URL root | `backend/config/` remains the single `ROOT_URLCONF` / settings module |
| Security-relevant settings computed only under `DEBUG=false` (CSP, HSTS, secure cookies, Permissions-Policy) must actually be issue-free at real process boot, not just look correct in source | CI `deploy-check` job (`.github/workflows/ci.yml`) runs `manage.py check --deploy` under a simulated `DEBUG=false` environment on every push/PR |
| `django-axes` must lock out and must reset on success | `AxesLockoutTest` in `backend/apps/core/tests.py` exercises the real login flow, not just the setting values |

## 7. Decisions
None recorded yet — no ADRs exist for this module as of this audit.

## 8. Glossary
| Term | Meaning in this module |
| :--- | :--- |
| Complexity validator | A Django `AUTH_PASSWORD_VALIDATORS` entry enforcing character-class rules on new passwords, distinct from length/similarity/breach checks. |
| Stub file | A Django-generated file left at its scaffolded default content (`models.py`, `views.py`, `admin.py` here) — present but not yet implementing project logic. |

---
*A module without a ratified Blueprint cannot enter Execution (agents.md §0). C4 Level 3 (Component diagram) required here if this module qualifies per `rules/documentation_standard.md §2.1` — see `**C4 Level Override**` for a manually-justified exception. `core` is currently the only declared container under `backend/apps/`, below the 5-container safety floor, so Level 3 stays advisory.*
