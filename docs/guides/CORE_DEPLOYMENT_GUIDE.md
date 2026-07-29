# 🧭 How-to: Deploy the containerized backend
**File**: `docs/guides/CORE_DEPLOYMENT_GUIDE.md` (RA-06 Option B naming)
**Module**: CORE

---

## 1. Goal
Run the production `Dockerfile` image (locally or on a real host) instead of the day-to-day `venv`-based development flow. See `docs/architecture/CORE_BLUEPRINT.md` for why the image is shaped this way (multi-stage, non-root, whitenoise, entrypoint order).

## 2. Prerequisites
- Docker and Docker Compose installed.
- `.env` and `config.toml` created from their `.example` templates (see the main [README](../../README.md#3-toml-configuration)) — this guide does not repeat that setup.
- Every variable in the README's [Environment Variable Descriptions](../../README.md#11-environment-variable-descriptions) set via whatever secret-management mechanism your target actually uses — never baked into the image (`config.toml` only ever contains `$VARIABLE_NAME` placeholders, see `Dockerfile`).

## 3. Steps

1. Run everything containerized, locally:
   ```bash
   docker-compose up -d
   ```
   This starts both `db` (Postgres) and `backend` (this Django app, built from the repo's `Dockerfile`). The backend container runs `manage.py migrate` and `manage.py collectstatic` automatically on every start (see `docker-entrypoint.sh`) before starting `gunicorn`.

   This is different from the day-to-day development flow documented in the main README, which runs Django outside Docker (via `venv`) against just the `db` service (`docker-compose up -d db`) for faster iteration — that flow is unaffected and still the recommended one for active development.

2. Build the image for a registry:
   ```bash
   docker build -t <your-registry>/<your-image>:<tag> .
   docker push <your-registry>/<your-image>:<tag>
   ```

3. Before setting `DEBUG=false`: `SECURE_SSL_REDIRECT=True` and the rest of the production-hardening block (`backend/config/settings.py`, Section 3) assume a TLS-terminating reverse proxy sits in front of this container — nginx, Caddy, Traefik, or your cloud provider's load balancer. `gunicorn` itself does not terminate TLS. Without a proxy in front, plain HTTP requests get redirected to HTTPS, which nothing is listening on — the app becomes unreachable.
   - **If your proxy terminates TLS and forwards over plain HTTP internally**: set `TRUST_PROXY_SSL_HEADER="true"` in `config.toml`/`.env`, but *only* if you control that proxy and it strips/overwrites any client-supplied `X-Forwarded-Proto` header — see the warning already in `.env.example`.

- **If deploying to a VPS / any generic Docker host**: `docker-compose up -d` (adjust `.env` for the real domain, set `DEBUG=false`, put a reverse proxy in front for TLS).
- **If deploying to Railway / Render / Fly.io**: point the platform at this repo's `Dockerfile` (all three support "deploy from Dockerfile" natively), set the required env vars via the platform's secret manager, and add a Postgres addon/service — the app reads `POSTGRES_*` the same way regardless of who's running Postgres. All three terminate TLS for you, so `TRUST_PROXY_SSL_HEADER="true"` is typically correct.
- **If deploying to Kubernetes**: build and push the image, run it as a `Deployment` with a `Service` on port 8000, use a `Secret` for the env vars, and either an `Ingress` (with your own TLS/cert-manager setup) or a cloud load balancer in front. For more than one replica, move `migrate` out of the entrypoint into a `Job`/init step run once per release (see the tech-debt note below).

## 4. Verify it worked
```bash
docker ps   # backend and db both show a "healthy" status
curl -I http://localhost:8000/admin/login/
```
Expected output: `200 OK` from the `curl`, and both containers report `healthy` in `docker ps`.

## 5. If something goes wrong
| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| `backend` container restarts in a loop, log shows `ImproperlyConfigured` | A required env var (`DJANGO_SECRET_KEY`, `POSTGRES_*`, etc.) isn't set, or a boolean field isn't exactly `"true"`/`"false"` | Check `docker logs <container>` for the exact variable named in the traceback |
| `backend` can't reach the database | `POSTGRES_HOST`/`POSTGRES_PORT` pointing at the host-mapped values instead of the container-internal ones | `docker-compose.yml` already overrides these for the `backend` service (`POSTGRES_HOST: db`, `POSTGRES_PORT: "5432"`) — if running the image outside this compose file, set them yourself to the DB's actual internal host/port |
| App unreachable after setting `DEBUG=false` | No TLS-terminating proxy in front, so `SECURE_SSL_REDIRECT` redirects to a port nothing is listening on | Put a reverse proxy in front, or don't flip `DEBUG` until one exists |
| Migrations race / partial schema when scaled to multiple replicas | `docker-entrypoint.sh` runs `migrate --noinput` on every start — fine for one replica, not for several starting in parallel | Move `migrate` out of the entrypoint into a separate one-off release step (most platforms — Railway, Render, Fly.io, Kubernetes Jobs — have a mechanism for this) |
| Uploaded files disappear after a redeploy | `MEDIA_ROOT` (`backend/mediafiles/`) isn't a persisted volume by default — `apps.core` has no upload model yet, so this isn't wired up speculatively | Mount a volume for `backend/mediafiles/`, or use external object storage (S3-compatible) for anything beyond a single host |

---
*See also: `docs/architecture/CORE_BLUEPRINT.md` (Reference) · related guides in `docs/guides/`.*
