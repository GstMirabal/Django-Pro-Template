# syntax=docker/dockerfile:1

# ==============================================================================
# BUILDER — installs dependencies into an isolated venv. Toolchain (compiler
# headers for argon2-cffi-bindings/cffi) never reaches the final image.
# ==============================================================================
FROM python:3.13-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==26.0.0 whitenoise==6.12.0

# ==============================================================================
# FINAL — minimal runtime image, non-root user.
# ==============================================================================
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd -r django && useradd -r -g django -d /app django

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY backend/ backend/
COPY config.toml.example ./config.toml
COPY docker-entrypoint.sh ./

RUN chmod +x docker-entrypoint.sh \
    && mkdir -p backend/staticfiles backend/mediafiles backend/logs \
    && chown -R django:django /app

USER django
WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 8000), timeout=3)" || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]
