# 📜 ADR-0005: Declare a cache backend explicitly, with a per-process fallback
**Status**: `Accepted`
**Date**: 2026-08-01
**Triggers**: 3, 6 (`rules/documentation_standard.md §3.1`)

---

## 1. Context

This template declared no `CACHES` setting, so Django applied its implicit
default: a per-process `LocMemCache`.

That default is adequate while nothing shares state across workers, and this
template ships no application that does. It stops being adequate the moment one
is installed. The failure has a specific shape worth stating, because it is the
reason this decision exists at all:

- A per-process cache is a dictionary inside one worker. Under Gunicorn, uWSGI
  or more than one container, a second request reaches a different process with
  a different dictionary.
- Anything using the cache as a source of truth — single-use tokens, rate-limit
  counters, step-up grants — therefore *appears* to work under a single worker
  and silently loses its guarantee in production.
- Nothing raises. There is no error, no warning, and no failing test. The
  control is simply not enforced.

`django-users-app` is the concrete case: it holds TOTP anti-replay markers and
step-up grants in the cache, and its own
[ADR-0001](https://github.com/GstMirabal/django-users-app/blob/main/docs/decisions/ADR-0001-shared-cache-backend.md)
records why it needs a shared backend. This decision is the other side of that
requirement: what the scaffold owes an application that has one.

## 2. Decision

Declare `CACHES` explicitly. Use Redis when `REDIS_URL` is configured, and fall
back to `LocMemCache` when it is not.

The fallback is deliberate and is the part most likely to be questioned. A hard
failure would be defensible for a project that needs a shared cache, but this
is a template that ships nothing requiring one, and refusing to start without
Redis would impose a service on every consumer — including a developer running
the suite. An application that genuinely depends on cross-worker state is the
right place for that hard requirement, and `django-users-app` states it in its
own contract.

What the explicit declaration buys is visibility. A project reading
`settings.py` sees which backend it is on and where the switch is, instead of
inheriting a per-process default it never chose and discovering it under load.

## 3. Consequences

| Consequence | Detail |
| :--- | :--- |
| A `REDIS_URL` in `config.toml` or the environment selects Redis. | No code change; the branch is in section 6.5. |
| Without it, the project still starts. | On the per-process backend, which is correct for a template with no cross-worker state of its own. |
| The fallback is silent. | It logs nothing, so a project that installs a cache-dependent app and forgets `REDIS_URL` gets the same silent degradation this ADR describes. That app is expected to check for it — `django-users-app` reports the omission through its own system checks. |
| `docker-compose.yml` carries a Redis service. | So the shared path is the one exercised locally, not a production-only configuration nobody has run. |

## 4. Alternatives considered

| Alternative | Why not |
| :--- | :--- |
| Leave the default implicit | The status quo. A project inherits a per-process cache without ever deciding to, which is how the failure above reaches production unnoticed. |
| Require `REDIS_URL`, fail without it | Correct for an application, wrong for a template: it forces a service on consumers that have no cross-worker state and makes the test suite depend on it. |
| Database-backed cache as the fallback | Shared across workers, so it removes the silent failure — but it puts cache traffic on the primary database, which is a performance decision this template should not make for its consumers. |

---
*Referenced from `docs/architecture/CONFIG_BLUEPRINT.md` §5.*
