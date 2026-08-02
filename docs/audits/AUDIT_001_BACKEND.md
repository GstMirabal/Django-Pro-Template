# 🔍 Audit Report: backend — Sprint #001
**Sprint**: #001
**Date**: 2026-07-31
**Commit**: 221ec9b
**Method**: full protocol, executed rather than read

---

## Method

Eleven techniques, each included because it found a real defect in a sibling repository that reading the code did not. Findings below are numbered `F-001`+ and classified by severity.

| Technique | Result here |
| :--- | :--- |
| Resolve every logger's handlers at runtime | **F-001** |
| Boot with `DEBUG=False` and the full production stack | Clean, after F-003 |
| Execute the suite rather than assume it exists | 13 pass (harness added this sprint) |
| Construct every registered admin form and inline formset | Clean — 5 admins, 0 failures |
| Check the library's real signature, not memory | No misuse found |
| Contrast each docstring against behaviour | Documentation verified accurate |
| Fresh virtualenv with only `requirements.txt` | Clean — no undeclared dependency |
| Grep for weak RNG on credential paths | None — no `random.*` in `backend/` |
| Contrast the graph against the documentation | Full coverage: every `backend/**.py` documented |
| Review the whole history, not just the tree | No secret ever committed |
| Reproduce the documented setup in a clean checkout | **F-002** |

---

## Findings

### F-001 · Application loggers reach no handler — **High**, latent

`LOGGING['loggers']` declares only `django` and `project`. Every module calling `logging.getLogger(__name__)` produces a name under `apps.*`, `config.*` or `utils.*`, none of which matches. Verified by resolving the handler chain at runtime:

| Logger | Handlers |
| :--- | :--- |
| `apps.core.validators` | `[]` — discarded |
| `apps.core.views` | `[]` — discarded |
| `config.settings` | `[]` — discarded |
| `django` | `StreamHandler`, 2× `RotatingFileHandler` |

**Latent, not active**: no file in `backend/` currently calls `getLogger`, so nothing is being lost today. It becomes active the moment any module logs — which is guaranteed, because the `users` app scheduled for this project logs decryption failures, replay-attack warnings and its anonymisation audit trail.

The same defect in the sibling repository silently discarded a `CRITICAL` on encryption-key mismatch.

**Fix**: register the `apps` and `utils` prefixes against the existing handlers.

### F-002 · Optional boolean keys could not fall back to their default — **High**, fixed this sprint

`config.toml.example` declares every optional key as `KEY = "$KEY"`. `envtoml` interpolates an unset variable to an **empty string**, so the key is present and `dict.get(key, 'false')` never reaches its fallback. `_parse_strict_bool` received `''` and refused to guess.

Following the project's own README — copy `config.toml.example`, set the required variables — aborted startup on `TRUST_PROXY_SSL_HEADER`. CI masked it by setting both optional flags explicitly.

**Fixed**: `_parse_strict_bool` takes a keyword-only `default`, used when the value is absent or empty. Verified in a clean checkout with no `.env` and neither flag set.

### F-003 · `.env` was loaded only by `manage.py` — **High**, fixed this sprint

`envtoml` interpolates `$VAR` from `os.environ` while reading `config.toml`, so the environment must be populated before that read, for every entrypoint. It was populated in `manage.py` alone.

| Entrypoint | Before |
| :--- | :--- |
| `manage.py` | boots |
| WSGI (gunicorn) | `ImproperlyConfigured` |
| ASGI | `ImproperlyConfigured` |
| pytest | `ImproperlyConfigured` |

Docker hid it: container runtimes inject variables directly and never read the file. A gunicorn deployment on a VM with a `.env` file did not start.

**Fixed**: moved into `settings.py` with `os.environ.setdefault`, so a variable already in the real environment still wins.

### F-004 · No health endpoint — **Medium**

`backend/apps/core/views.py` contains only `# Create your views here.`. There is no liveness or readiness probe, so an orchestrator has nothing to poll and a degraded dependency is invisible until a user request fails.

### F-005 · No `CACHES` configuration — **Medium**

No `CACHES` block exists, so Django falls back to per-process `LocMemCache`. Harmless today, since nothing in this project uses the cache. It stops being harmless the moment an app needing shared state is installed: the `users` app relies on the cache for TOTP anti-replay and step-up authentication, both of which silently fail across workers on a per-process backend.

### F-006 · `.gitignore` missed the real log directory — **Low**, fixed this sprint

The rule covered `/backend/logs/` while the directory the application creates is `/logs/` at the repository root. Log files were one `git add -A` away from being tracked.

### F-007 · Workflows declare no `permissions` — **Medium**

Reported independently by CodeQL (`actions/missing-workflow-permissions`, 2 alerts). Neither job in `.github/workflows/ci.yml` declares a `permissions:` block, so both inherit the repository default for `GITHUB_TOKEN`, which may include write scopes a lint-and-test job never needs.

### F-008 · `dependabot.yml` groups nothing — **Low**

The configuration covers pip, github-actions and docker on a weekly interval, with no grouping and no `open-pull-requests-limit`. Now that Dependabot is enabled at the repository level, a routine week can open one pull request per package.

---

## What was verified and found correct

Stated explicitly, because an audit that only lists problems misrepresents the subject:

- **The existing documentation is accurate.** Every claim in `CORE_BLUEPRINT.md` was checked against the code: whitenoise in the middleware stack, `django-permissions-policy`, CSP in the 4.0 dict format, `CROSS_SITE_FRONTEND`, opt-in `TRUST_PROXY_SSL_HEADER`, the stub state of `models.py`/`views.py`/`admin.py`, `AxesLockoutTest` exercising the real login flow, the `deploy-check` CI job, and a multi-stage non-root `Dockerfile`. No false statement was found.
- **Documentation coverage is complete.** Every `.py` file under `backend/` is described somewhere in `docs/`.
- **No secret has ever been committed.** Confirmed over the whole history, and independently by GitHub secret scanning: zero alerts.
- **The dependency set is honest.** A fresh virtualenv with only `requirements.txt` passes `manage.py check`.
- **Django 6.0.7 required no code change.** Ten dependency bumps, suite and both check runs green.
- **The security posture is genuinely strong**: strict boolean parsing on four security-relevant settings, five-validator password chain including breach-corpus lookup, Axes lockout covering `/admin/login/`, CSP and Permissions-Policy under `DEBUG=False`, opt-in trust boundaries.

## Summary

| Severity | Open | Fixed this sprint |
| :--- | ---: | ---: |
| High | 1 (F-001) | 2 (F-002, F-003) |
| Medium | 3 (F-004, F-005, F-007) | — |
| Low | 1 (F-008) | 1 (F-006) |

F-001, F-004 and F-005 are the three that block installing the `users` app, and are scheduled for P1.5.
