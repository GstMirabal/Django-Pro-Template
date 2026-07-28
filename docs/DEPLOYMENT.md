# Deployment Guide

This project ships a production-ready `Dockerfile` and an optional `backend` service in `docker-compose.yml`. This guide covers running that image, not a specific hosting platform's exact configuration — as a generic template, committing to one platform's manifest format here would be presumptuous about where a fork of this repo actually gets deployed.

## Running everything containerized, locally

```bash
cp .env.example .env      # fill in real values
cp config.toml.example config.toml
docker-compose up -d
```

This starts both `db` (Postgres) and `backend` (this Django app, built from the repo's `Dockerfile`). The backend container runs `manage.py migrate` and `manage.py collectstatic` automatically on every start (see `docker-entrypoint.sh`) before starting `gunicorn`.

This is different from the day-to-day development flow documented in the main [README](../README.md#4-database-initialization), which runs Django outside Docker (via `venv`) against just the `db` service (`docker-compose up -d db`) for faster iteration — that flow is unaffected and still the recommended one for active development.

## Building the image for a registry

```bash
docker build -t <your-registry>/<your-image>:<tag> .
docker push <your-registry>/<your-image>:<tag>
```

## Required environment variables in production

Same table as the [README's Environment Variable Descriptions](../README.md#11-environment-variable-descriptions) — every variable listed there must be set via whatever secret-management mechanism your platform provides (not baked into the image; `config.toml` only ever contains `$VARIABLE_NAME` placeholders, see `Dockerfile`).

## Read this before setting `DEBUG=false`

`SECURE_SSL_REDIRECT=True` and the rest of the production-hardening block (`backend/config/settings.py`, Section 3) assume a TLS-terminating reverse proxy sits in front of this container — nginx, Caddy, Traefik, or your cloud provider's load balancer. `gunicorn` itself does not terminate TLS. Without a proxy in front:
- Plain HTTP requests get redirected to HTTPS, which nothing is listening on — the app becomes unreachable.
- If your proxy does terminate TLS and forwards requests over plain HTTP internally, set `TRUST_PROXY_SSL_HEADER="true"` in `config.toml`/`.env` **only if you control that proxy and it strips/overwrites any client-supplied `X-Forwarded-Proto` header** — see the warning already in `.env.example`.

## Database migrations on every start

`docker-entrypoint.sh` runs `migrate --noinput` on every container start. This is the simplest default for a single-replica deployment (the common case for a fork of this template) and is idempotent — safe to run repeatedly. If you scale `backend` to multiple replicas, running `migrate` from every replica in parallel on startup can race; run it as a separate one-off release step instead (most platforms — Railway, Render, Fly.io, Kubernetes Jobs — have a mechanism for this) and remove it from the entrypoint.

## Media file uploads

`MEDIA_ROOT` (`backend/mediafiles/`) is not a persisted volume in `docker-compose.yml` by default — files written there are lost when the `backend` container is recreated. `apps.core` doesn't have any model that uploads files yet, so this isn't wired up speculatively. If your fork adds file uploads, either mount a volume for `backend/mediafiles/` or, for anything beyond a single host, use external object storage (S3-compatible) instead of local disk.

## Notes for common targets

These are pointers, not configs — the image built from this repo's `Dockerfile` is what you deploy; each platform just needs to be told how to run it.

- **VPS / any Docker host**: `docker-compose up -d` (adjust `.env` for the real domain, set `DEBUG=false`, put a reverse proxy in front for TLS).
- **Railway / Render / Fly.io**: point the platform at this repo's `Dockerfile` (all three support "deploy from Dockerfile" natively), set the required env vars via the platform's secret manager, and add a Postgres addon/service — the app reads `POSTGRES_*` the same way regardless of who's running Postgres. All three terminate TLS for you, so `TRUST_PROXY_SSL_HEADER="true"` is typically correct.
- **Kubernetes**: build and push the image, run it as a `Deployment` with a `Service` on port 8000, use a `Secret` for the env vars, and either an `Ingress` (with your own TLS/cert-manager setup) or a cloud load balancer in front. For more than one replica, move `migrate` out of the entrypoint into a `Job`/init step run once per release (see above).
