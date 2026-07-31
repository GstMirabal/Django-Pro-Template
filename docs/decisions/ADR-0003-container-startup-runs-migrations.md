# 📜 ADR-0003: Migrations and static collection run at container start
**Status**: `Accepted`
**Date**: 2026-07-31
**Triggers**: 1, 6 (`rules/documentation_standard.md §3.1`)

---

## 1. Context

`migrate` and `collectstatic` both need things that do not exist during `docker build`: real environment variables, and a reachable database. Neither can run at image-build time.

They have to run somewhere. The candidates are the container entrypoint, a separate one-off job in the orchestrator, or a manual step in the deployment runbook.

## 2. Decision

`docker-entrypoint.sh` runs both before handing off to the application server:

```sh
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
```

`set -e` means a failing migration aborts startup rather than serving traffic against a schema the code does not expect.

## 3. Consequences

**Easier.** A single-container deployment needs no runbook: `docker run` is a complete deploy. `set -e` turns a broken migration into a container that refuses to start, which orchestrators surface as a failed rollout instead of a silently degraded service.

**Harder, and this is the significant one.** With more than one replica, **every replica runs `migrate` concurrently on the same database at rollout**. Django takes a lock per migration, so the usual outcome is that one applies and the others wait and no-op — but that is a race whose safety depends on the migrations themselves being well-behaved, and it is not a guarantee this project can make on behalf of arbitrary future migrations. A data migration that is not idempotent, or one that holds a long lock, turns a routine rollout into an outage.

**Any deployment beyond one replica must move `migrate` out of the entrypoint** into a pre-deploy job (Kubernetes `Job`, ECS one-off task, `release` phase) and keep only `collectstatic` here. That caveat lives in `docs/guides/CORE_DEPLOYMENT_GUIDE.md` and is the reason this decision is recorded rather than left implicit.

`collectstatic` on every start also adds seconds to boot and repeats work already done by the previous replica. Acceptable for the default shape; wasteful at scale.

## 4. Deciders

Repository owner.

## 5. Considered Options

| Option | Pros | Cons |
| :--- | :--- | :--- |
| **Both in the entrypoint** (chosen) | `docker run` is a complete deploy; no runbook for the default shape | Concurrent `migrate` across replicas; repeated `collectstatic` |
| `migrate` in a pre-deploy job, `collectstatic` in the entrypoint | Correct for any replica count | Requires orchestrator-specific configuration the template cannot ship generically |
| Both at build time | Fastest start | Impossible: neither has a database or real environment during `docker build` |
| Neither — document a manual step | No surprises | A forgotten `migrate` serves traffic against the wrong schema, which is worse than any option above |

---
*Immutable once Accepted — a changed decision gets a new ADR that supersedes this one, never an in-place edit (`rules/documentation_standard.md §3`).*
