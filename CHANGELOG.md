# Changelog

All notable changes to Django Pro Template. This file is the **Master Ledger** (agents.md §0): every Sprint Closeout appends its sprint entry under `[Unreleased]`; every deployment seals that section as `[vX.Y.Z] - date` immediately before tagging.

Format: [Keep a Changelog](https://keepachangelog.com/) · Versioning: [SemVer](https://semver.org/).

> Jurisdiction note: framework changes live in `.agents/CHANGELOG.md`, never here. When the `.agents` pin is updated, this ledger records only the bump (e.g. `chore(deps): pin .agents to v3.1.0 #[Sprint_ID]`).

## [Unreleased]

### Fixed
- **`.env` now loads for every entrypoint.** It was loaded only by `manage.py`, so WSGI (gunicorn), ASGI, pytest and any plain script booted with an empty environment and failed on `DJANGO_SECRET_KEY`. Docker hid this — container runtimes inject the variables directly — but a gunicorn deployment on a host with a `.env` file did not start. #001
- **Optional boolean keys reach their default.** `config.toml.example` declares each as `KEY = "$KEY"`, so `envtoml` interpolates an unset variable to an empty string; the key is present and `dict.get(key, fallback)` never reaches its fallback. Following this project's own README aborted startup on `TRUST_PROXY_SSL_HEADER`. #001
- **Application loggers reach a handler.** `LOGGING` declared only `django` and `project` while every module calls `getLogger(__name__)`, yielding `apps.*`, `config.*` and `utils.*` — verified at runtime to resolve to an empty handler list. #001
- **`.gitignore` covers the real log directory.** The rule named `/backend/logs/` while the application creates `/logs/`. #001
- Workflows declare `permissions: contents: read` instead of inheriting the repository default for `GITHUB_TOKEN` (CodeQL). #001

### Added
- **`GET /health/`** — liveness and readiness probe reporting database and cache independently, `200` healthy and `503` degraded. Contract in `docs/contracts/CORE_CONTRACT.md`. #001
- **`core.E001` admin-integrity system check** constructing every registered admin form and inline formset at startup. Django's own checks do not validate inline `fields`, so that class of defect otherwise reaches production as a 500. #001
- **Explicit `CACHES`** with optional `REDIS_URL`, and a Redis service in `docker-compose.yml` under the `cache` profile. Deliberately not a hard failure when unset: this template ships no app that uses the cache. #001
- **pytest harness** (`pytest.ini` + `config/settings_test.py`) running on an in-RAM SQLite database. The 13 existing `TestCase` classes run unmodified. #001
- **Four retroactive ADRs** under `docs/decisions/` — strict boolean configuration, opt-in trust boundaries, container startup migrations, layered password policy. #001
- **Reusable CI workflow** (`.github/workflows/django-ci.yml`) for the repositories derived from this template to call rather than copy. #001
- `docs/audits/AUDIT_001_BACKEND.md`, `docs/roadmaps/GLOBAL_ROADMAP.md`, `docs/contracts/CORE_CONTRACT.md`, and the sprint log. #001

### Changed
- **Django 5.2.16 → 6.0.7**, across ten dependency bumps, with no application-code change. #001
- `docs/active_state.json` is now tracked: `docs_freshness_check.py` reads it, and `start_workflow.md` treats its absence as an un-onboarded host, so ignoring it made every fresh clone re-run the onboarding scaffold. #001
- Governance: `topology_map` as flat string paths and `current_sprint` carrying `last_audit_sprint`, which is what the freshness gate actually reads. #001
- Session closeout (`/agents:close`): renamed `docs/DEPLOYMENT.md` to `docs/guides/CORE_DEPLOYMENT_GUIDE.md` (RA-06 Option B naming — how-to guides live at `docs/guides/[MODULE]_[TASK]_GUIDE.md`) and restructured it to the How-to template (Goal/Prerequisites/Steps/Verify/Troubleshooting); updated every cross-reference. Purged 3 empty scaffold directories (`docs/contracts/`, `docs/roadmaps/backend/core/`, `docs/sprints/backend/core/`) per RA-07. #000
- Adopted Token-Optimized Agent Pipeline governance (v4.2.1) — onboarding scenario: C (mature project, no prior agentic traces). #000
- CI (`.github/workflows/ci.yml`): lint, tests, and a `manage.py check --deploy` run booted with a simulated `DEBUG=false` on every push/PR. #000
- `django-axes` brute-force login protection, tuned to lock out `(username, ip_address)` pairs (not IP alone) and reset the failure count on a successful login. #000
- `django-permissions-policy`, replacing a dead, unrecognized `SECURE_PERMISSIONS_POLICY` setting that never sent a header. #000
- `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOW_CREDENTIALS`, and an opt-in `CROSS_SITE_FRONTEND` flag (`SameSite=None` cookies) so a decoupled frontend can authenticate by session across origins. #000
- Opt-in `SECURE_PROXY_SSL_HEADER` (`TRUST_PROXY_SSL_HEADER`), and configurable `LANGUAGE_CODE`/`TIME_ZONE` (previously hardcoded to a specific region). #000
- `.github/dependabot.yml` (pip + GitHub Actions, weekly) and `requirements-dev.txt` (`ruff`). #000
- A functional test suite for the above: `django-axes` lockout exercised via the real login flow, and CSP/Permissions-Policy header regression tests. #000
- A banner (`docs/assets/logo/django_pro_template_banner.svg`) and CI status badge on the README. #000
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/config.yml`, `.editorconfig`, `.python-version`. Adapted the bug-report issue template (was asking about "Browser"/"Smartphone" fields, irrelevant to a backend project). #000
- `Dockerfile` (multi-stage, non-root, own `HEALTHCHECK`) and `docker-entrypoint.sh` (`migrate` + `collectstatic` on every start) for a generic, production-ready container image. `whitenoise` for static file serving. Optional `backend` service in `docker-compose.yml`; the documented local-dev flow (`docker-compose up -d db` + Django via `venv`) is unchanged. `docker` ecosystem added to Dependabot. `docs/guides/CORE_DEPLOYMENT_GUIDE.md` — deploy guidance (Docker Compose, VPS, Railway/Render/Fly.io, Kubernetes) without committing to one platform's exact config. #000
- Trimmed the production image: drop `__pycache__` and `pip` from the builder-installed venv (never needed after install, ~35MB) and the base image's own system-level `pip` (unreachable at runtime, this app only ever runs from `/opt/venv` — smaller attack surface, not a further size win since it lives in a base-image layer this Dockerfile can only mask, not shrink). 307MB → 270MB, re-verified end-to-end (build, migrate, collectstatic, gunicorn, static asset serving) after each change. #000

### Fixed (found while verifying the containerized deploy against a real build)
- `whitenoise.storage.CompressedManifestStaticFilesStorage` requires `collectstatic` to have already run — without it, *any* `{% static %}` reference (including the Django admin's own templates) raised `ValueError`, breaking `manage.py test`/`runserver` in local development, which never runs `collectstatic`. Now only used when `DEBUG` is false; `WHITENOISE_USE_FINDERS`/`WHITENOISE_AUTOREFRESH` serve static files straight from source in development instead. #000
- The `backend` service's DB connection used `POSTGRES_PORT` from `.env` for its *internal* connection to `db` — correct only by coincidence when that value happens to be the Postgres default (5432). Changing `POSTGRES_PORT` to avoid a host port conflict (a normal thing to do) would silently break the `backend`→`db` connection. Now explicitly pinned to `5432` (the container's actual internal port) for that one connection, independent of whatever host port is published externally. #000

### Fixed
- `DEBUG`/`EMAIL_USE_TLS` silently evaluating truthy for a capitalized `"False"` value (the exact format the project's own `.env.example` documented) — production hardening (HSTS, secure cookies, SSL redirect) never activated. Now parsed strictly, failing loudly on anything but `true`/`false`. #000
- `django-csp` 4.0 config-format incompatibility that would have crashed the app at the first production boot with a system check `Error`, once the `DEBUG` bug above was fixed. #000
- Database credentials interpolated into the connection URL without URL-encoding. #000
- Leftover "cryptobot" branding in `apps/core/validators.py`, `.env.example`, and `config.toml.example`. #000
- `README.md`: wrong `config.toml` location, missing `cp config.toml.example config.toml` step, stale manual URL-encoding instruction, a reference to a nonexistent `src/` folder, out-of-sync embedded config examples, and leftover editorial notes. #000
- `SECURITY.md`: replaced generic GitHub boilerplate with a real vulnerability-reporting process (GitHub Security Advisories). #000
- 49 known CVEs across pinned dependencies (`pip-audit`): `Django` 5.2.7 → 5.2.16, `idna` 3.11 → 3.18, `sqlparse` 0.5.3 → 0.5.5. #000
- `docker-compose.yml`'s `db` service: unpinned `postgres:15` → pinned `postgres:15.10`, Postgres port published to all interfaces → `127.0.0.1` only, no healthcheck/restart policy → both added. #000
- `.gitignore` missing entries that left `identity.config.json`, `.mcp.json`, and `.agent_state/` untracked but not ignored (a careless `git add -A` would have committed them — `identity.config.json` in particular is meant to hold real contact info). #000
- CI (`lint-and-test` and `deploy-check`) failing on every push: the `CROSS_SITE_FRONTEND` opt-in strict-bool setting was never added to `ci.yml`'s env blocks when introduced, so it resolved to an empty string and `_parse_strict_bool` refused to boot Django. See `docs/hotfixes/H-001-CI.md`. #H-001-CI
- `envtoml` 0.4.0 (Dependabot PR #6) broke Django boot entirely (`TypeError: File must be opened in binary mode`): `config.toml` was opened in text mode, incompatible with the new file-handling contract. Now opened in binary mode. See `docs/hotfixes/H-002-Backend.md`. #H-002-Backend

## [0.1.0] - 2026-07-27
_Seed entry: state of the project at governance adoption (Scenario C — mature project, no agents)._

Audited via Full Reverse Engineering of the pre-existing codebase (no functional code changed during onboarding):
- Django 5.2 backend (`backend/`), single deployable unit, entrypoint `backend/manage.py`.
- Configuration loaded from `config.toml` (templated from `.env`), with fail-fast validation of `DJANGO_SECRET_KEY`, database components, and production-only `ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`/email settings.
- Hardened production security headers (HSTS, CSP, referrer/permissions policy, secure cookies) applied whenever `DEBUG` is false.
- Structured logging: console + rotating file (`project.log`) + rotating JSON file (`project.json`), UTC timestamps.
- Single local app `apps.core` registered — a placeholder today (`models.py`/`views.py`/`admin.py` are unmodified stubs) except for a real `PasswordComplexityValidator` wired into `AUTH_PASSWORD_VALIDATORS`.
- `AUTH_USER_MODEL` customization left commented out — default Django `User` model still in effect (flagged as tech-debt in `docs/walkthroughs/CORE_WALKTHROUGH.md`).
