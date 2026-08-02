# 🏛️ Blueprint: CONFIG
**File**: `docs/architecture/CONFIG_BLUEPRINT.md` (RA-06 Option B naming)
**Module**: CONFIG
**Last Audit Sprint**: #002
**Last Audit Date**: 2026-08-01

---

## 1. Introduction & Goals

The project's configuration surface. It resolves settings from a TOML file with
environment interpolation, refuses to boot on a missing secret, and applies a
different security posture depending on `DEBUG`.

## 2. Context & Scope

| Aspect | Detail |
| :--- | :--- |
| **Upstream dependencies** | `envtoml` + `config.toml`, `django`, `axes`, `csp`, `corsheaders`, `whitenoise`, `python-json-logger`. |
| **Downstream consumers** | Every runtime component. `apps.core` reads database, cache and logging settings from here; an installed application such as `django-users-app` reads `AUTH_USER_MODEL`, `MASTER_KEY`, `ENCRYPTION_PEPPER` and the cache configuration. |

## 3. Building Block View

| Aspect | Detail |
| :--- | :--- |
| **Owns** | `backend/config/` — `settings.py` (718 lines, twelve numbered section headers), `settings_test.py`, `urls.py`, `wsgi.py`, `asgi.py`, `__init__.py`. |
| **Must not touch** | `backend/apps/*/` business logic, application migrations. |

`settings.py` is a single module, not a package. Its sections are numbered, and
each depends only on values the earlier ones produced:

| § | Concern |
| :--- | :--- |
| 1 | `BASE_DIR`, `.env` loading, `config.toml` resolution |
| 2 | Core security: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, CSP, CORS |
| 3 | Production-only hardening, applied when `DEBUG` is false |
| 4 | Installed apps, authentication backends, `django-axes` |
| 5 | Middleware order, root URLconf, templates, WSGI |
| 6 | Database |
| 6.5 | Cache |
| 7 | Password validators and hashers |
| 8 | User model, i18n, static and media files |
| 9 | Email |
| 10 | Default primary key |
| 11 | Logging |

## 4. Runtime View

Configuration resolves in a fixed order, ending in a hard failure:

1. `.env` is read into `os.environ` with `setdefault`, so a value already
   present in the real environment wins. The load happens in `settings.py`,
   which every entrypoint imports — `manage.py`, `gunicorn`, `wsgi` and `asgi`.
2. `config.toml` is parsed by `envtoml`, which expands `$VAR` references
   against `os.environ`.
3. A missing required secret raises at import. The process does not start with
   a placeholder in place of a key.

Booleans go through `_parse_strict_bool`, which accepts only a documented set of
literals and raises on anything else — see
[ADR-0001](../decisions/ADR-0001-strict-boolean-configuration.md). A `DEBUG`
that silently parsed as truthy would disable the whole of section 3.

## 5. Crosscutting Concepts

| Concept | Rule |
| :--- | :--- |
| **Configuration precedence** | Real environment first, `config.toml` second, hard failure third. Secrets are never committed; `config.toml.example` is the tracked shape. |
| **Middleware ordering** | `SecurityMiddleware` → `CSPMiddleware` → session → CORS → common → CSRF → auth → messages → clickjacking → `AxesMiddleware` last, so `request.user` is resolved before lockout accounting. |
| **Cache** | A shared backend when one is configured, with a per-process fallback. An application that needs cross-worker state declares that requirement itself — see [ADR-0005](../decisions/ADR-0005-shared-cache-backend.md). |
| **Axes username field** | `AXES_USERNAME_FORM_FIELD` is pinned to `'username'`. From axes 8 the default derives from the user model's `USERNAME_FIELD`, and a project that swaps in an email-login model would otherwise record every failed login as `username=None`. |
| **Logging** | `apps`, `config` and `utils` are registered as logger prefixes. Without them, `getLogger(__name__)` in any project module resolves to zero handlers. |

## 6. Architecture Decisions

| ADR | Subject |
| :--- | :--- |
| [ADR-0001](../decisions/ADR-0001-strict-boolean-configuration.md) | Strict boolean parsing |
| [ADR-0002](../decisions/ADR-0002-opt-in-trust-boundaries.md) | Opt-in trust boundaries |
| [ADR-0003](../decisions/ADR-0003-container-startup-runs-migrations.md) | Container startup runs migrations |
| [ADR-0004](../decisions/ADR-0004-layered-password-policy.md) | Layered password policy |
| [ADR-0005](../decisions/ADR-0005-shared-cache-backend.md) | Shared cache backend |

## 7. Quality Requirements

| Requirement | How it is verified |
| :--- | :--- |
| Every entrypoint boots with the same configuration. | `manage.py`, `wsgi`, `asgi` and `gunicorn` each start with `DEBUG=false` and a real `config.toml`. |
| Production hardening is reachable. | `manage.py check --deploy --fail-level WARNING` under `DEBUG=false` reports nothing. |
| A missing secret stops the process. | Unsetting a required key and importing settings raises. |
| Application loggers reach a handler. | Resolving handlers for `apps.*` at runtime returns a non-empty list. |

---
*Updated at every Sprint Closeout touching this module (RA-05).*
