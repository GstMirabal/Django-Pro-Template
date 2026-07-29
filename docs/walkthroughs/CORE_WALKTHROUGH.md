# 🏁 Walkthrough: CORE
**File**: `docs/walkthroughs/CORE_WALKTHROUGH.md` (RA-06 Option B naming)
**Last updated**: Sprint #000 (Security Hardening + Containerized Deploy — Rounds 1-4)

---

## 1. What was achieved
| Sprint | Milestone | Outcome |
| :--- | :--- | :--- |
| #000 | Legacy Onboarding (Full Reverse Engineering) | Pre-existing Django backend audited and documented under the `.agents` pipeline for the first time; no code changed. |
| #000 | Security Hardening (Rounds 1-3) | Fixed a silent `DEBUG` boolean-parsing bug, a `django-csp` 4.0 config-format incompatibility that would have crashed the app at production boot, and a dead `PERMISSIONS_POLICY` setting that never sent its header. Added `CSRF_TRUSTED_ORIGINS`/`CORS_ALLOW_CREDENTIALS`/opt-in `CROSS_SITE_FRONTEND` for decoupled-frontend session auth, opt-in `SECURE_PROXY_SSL_HEADER`, configurable `TIME_ZONE`/`LANGUAGE_CODE`, `django-axes` brute-force lockout (tuned to `(username, ip)` pairs with reset-on-success), CI (lint + tests + a real `DEBUG=false` boot check), Dependabot, and a functional test suite covering all of the above. Cleaned up leftover "cryptobot" branding. |
| #000 | Containerized Deploy (Round 4) | Added a production `Dockerfile` (multi-stage, non-root, own `HEALTHCHECK`) and `docker-entrypoint.sh` (`migrate` + `collectstatic` on every start), `whitenoise` for static files, an optional `backend` service in `docker-compose.yml`, hardened the `db` service (pinned patch, healthcheck, `127.0.0.1`-only port, restart policy), added the `docker` ecosystem to Dependabot, and wrote `docs/guides/CORE_DEPLOYMENT_GUIDE.md` (guide-level, not tied to one hosting platform). The existing local-dev flow (`docker-compose up -d db` + Django via `venv`) is unchanged. |
| (pre-`.agents`) | Django 5.2 project scaffolded | `config.toml`/`.env`-driven settings, structured (console + rotating file + JSON) logging, `apps.core` registered as the first local app. |
| (pre-`.agents`) | Password hardening | Custom `PasswordComplexityValidator` added alongside Django's built-in validators and `pwned_passwords_django`. |

## 2. Current state
The backend boots via `backend/manage.py` → `config.settings`, reading configuration from `config.toml` (itself templated from `.env`). `apps.core` is registered in `INSTALLED_APPS` but is functionally an empty skeleton: `models.py`, `views.py`, and `admin.py` remain Django's default stub comments, and no URL in `backend/config/urls.py` routes to it besides the Django admin site. The one real piece of app-level logic, `PasswordComplexityValidator`, sits alongside a project-level security stack that is now verified, not just present: CSP (`django-csp` 4.0 dict format), CORS/CSRF for a decoupled frontend, brute-force lockout (`django-axes`), and a `Permissions-Policy` header (`django-permissions-policy`) — all confirmed with a real Postgres-backed test run in this session, including a functional lockout test (5 failed logins → HTTP 429) and a live check that CSP doesn't break the Django admin UI. `manage.py check --deploy` under a simulated `DEBUG=false` environment now returns zero issues; this same check runs in CI on every push/PR. Implements: `docs/architecture/CORE_BLUEPRINT.md`.

## 3. Known limitations / tech debt
| Item | Marked as | Tracked where |
| :--- | :--- | :--- |
| `AUTH_USER_MODEL` is commented out in `settings.py` (`#AUTH_USER_MODEL = 'users.User'`) — project still runs on Django's default `User` model | `:tech-debt:` | Deliberate decision, not a bug — left for each fork to make explicitly, per the settings.py comment's own warning. Not tracked in a Sprint. |
| `apps.core` has no domain models/views yet — it is currently a placeholder app rather than a feature module | `:tech-debt:` | Not yet tracked in a Sprint |
| `mediafiles/` isn't a persisted volume in `docker-compose.yml` — fine today (`apps.core` uploads nothing), would need a volume or external object storage if a fork adds file uploads | `:tech-debt:` | Documented in `docs/guides/CORE_DEPLOYMENT_GUIDE.md`, not implemented speculatively |
| `migrate` runs automatically on every container start, which races if `backend` is ever scaled to multiple replicas | `:tech-debt:` | Documented in `docs/guides/CORE_DEPLOYMENT_GUIDE.md` as something to change (separate release step) before scaling beyond one replica |

No ADRs exist yet for this module, so none of the above are linked to a deliberate-decision ADR — they are simply the as-found state.

## 4. How to operate it
Minimum commands to run/verify the module (deterministic, prefixed paths per agents.md §3):

```bash
cd backend && python manage.py check
cd backend && python manage.py test apps.core
```

CI runs the equivalent (plus `ruff check .` and a `DEBUG=false` boot check) on every push/PR — see `.github/workflows/ci.yml`.

Fully containerized (builds and runs the production image locally): `docker-compose up -d` — see `docs/guides/CORE_DEPLOYMENT_GUIDE.md`.

---
*Updated at every Sprint Closeout touching this module (RA-05).*
