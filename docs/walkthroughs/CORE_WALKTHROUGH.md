# 🏁 Walkthrough: CORE
**File**: `docs/walkthroughs/CORE_WALKTHROUGH.md` (RA-06 Option B naming)
**Last updated**: Sprint #001 (Reference scaffold: audit, harness, Django 6)

---

## 1. What was achieved
| Sprint | Milestone | Outcome |
| :--- | :--- | :--- |
| #000 | Legacy Onboarding (Full Reverse Engineering) | Pre-existing Django backend audited and documented under the `.agents` pipeline for the first time; no code changed. |
| #000 | Security Hardening (Rounds 1-3) | Fixed a silent `DEBUG` boolean-parsing bug, a `django-csp` 4.0 config-format incompatibility that would have crashed the app at production boot, and a dead `PERMISSIONS_POLICY` setting that never sent its header. Added `CSRF_TRUSTED_ORIGINS`/`CORS_ALLOW_CREDENTIALS`/opt-in `CROSS_SITE_FRONTEND` for decoupled-frontend session auth, opt-in `SECURE_PROXY_SSL_HEADER`, configurable `TIME_ZONE`/`LANGUAGE_CODE`, `django-axes` brute-force lockout (tuned to `(username, ip)` pairs with reset-on-success), CI (lint + tests + a real `DEBUG=false` boot check), Dependabot, and a functional test suite covering all of the above. Cleaned up leftover "cryptobot" branding. |
| #000 | Containerized Deploy (Round 4) | Added a production `Dockerfile` (multi-stage, non-root, own `HEALTHCHECK`) and `docker-entrypoint.sh` (`migrate` + `collectstatic` on every start), `whitenoise` for static files, an optional `backend` service in `docker-compose.yml`, hardened the `db` service (pinned patch, healthcheck, `127.0.0.1`-only port, restart policy), added the `docker` ecosystem to Dependabot, and wrote `docs/guides/CORE_DEPLOYMENT_GUIDE.md` (guide-level, not tied to one hosting platform). The existing local-dev flow (`docker-compose up -d db` + Django via `venv`) is unchanged. |
| #001 | Reference scaffold | Established this repository as the backend scaffold the other Django hosts copy from. Full audit under the `.agents` protocol (`docs/audits/AUDIT_001_BACKEND.md`, 8 findings): fixed `.env` loading that only ran under `manage.py`, optional boolean keys that could never reach their default, application loggers that reached no handler, and a `.gitignore` rule pointing at the wrong log directory. Added a `/health/` endpoint, the `core.E001` admin-integrity system check, an explicit `CACHES` block with optional Redis, a pytest harness running on in-RAM SQLite, and four retroactive ADRs. Upgraded to Django 6.0.7 across ten dependency bumps with no code change. Extracted the pipeline to a reusable workflow. |
| (pre-`.agents`) | Django 5.2 project scaffolded | `config.toml`/`.env`-driven settings, structured (console + rotating file + JSON) logging, `apps.core` registered as the first local app. |
| (pre-`.agents`) | Password hardening | Custom `PasswordComplexityValidator` added alongside Django's built-in validators and `pwned_passwords_django`. |

## 2. Current state

The backend boots from any entrypoint — `manage.py`, WSGI, ASGI or pytest — reading configuration from `config.toml`, itself templated from the environment. Until Sprint #001 only `manage.py` populated that environment, so gunicorn on a host with a `.env` file did not start.

`apps.core` is no longer an empty skeleton. It owns `PasswordComplexityValidator`, a `/health/` endpoint probing database and cache independently, and a custom system check (`core.E001`) that constructs every registered admin form and inline formset at startup — catching a class of misconfiguration Django's own checks do not validate. `models.py` and `admin.py` remain deliberate stubs.

The project-level security stack is verified rather than merely present: CSP in `django-csp` 4.0 dict format, CORS/CSRF for a decoupled frontend, `django-axes` lockout tested against the real login flow, `Permissions-Policy`, and strict boolean parsing on the four security-relevant settings. `manage.py check --deploy` under a real `DEBUG=false` boot returns zero issues, and CI runs that same boot on every push.

Runs on Django 6.0.7. The suite is 19 tests on an in-RAM SQLite database, needing neither Docker nor a reachable PostgreSQL.

Implements: `docs/architecture/CORE_BLUEPRINT.md`.

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
