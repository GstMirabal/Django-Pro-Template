#!/bin/sh
# Runs on every container start (not at build time), once real env vars are
# available. Both steps are idempotent — safe to run again on restart.
#
# Single-replica default: with multiple replicas starting in parallel,
# concurrent `migrate` runs can race. If you scale this beyond one replica,
# run migrations as a separate release step instead — see docs/DEPLOYMENT.md.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
