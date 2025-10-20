#!/usr/bin/env bash
set -euo pipefail

MODE=${1:-web}

if [ "$MODE" = "web" ]; then
  echo "Starting uvicorn web server..."
  # Allow overriding host/port via env
  HOST=${HOST:-0.0.0.0}
  PORT=${PORT:-8000}
  exec uvicorn main:app --host "$HOST" --port "$PORT"
elif [ "$MODE" = "worker" ]; then
  echo "Starting celery worker..."
  # Allow passing extra args via environment variable CELERY_ARGS
  # Celery 5 requires the -A (app) option to be a global option (before 'worker').
  # We use CELERY_APP to explicitly set the app, and CELERY_WORKER_ARGS for worker flags.
  CELERY_APP=${CELERY_APP:-"celery_app.celery_app"}
  CELERY_WORKER_ARGS=${CELERY_WORKER_ARGS:-"--loglevel=info --concurrency=1"}
  exec celery -A ${CELERY_APP} worker ${CELERY_WORKER_ARGS}
else
  echo "Unknown mode '$MODE' - expected 'web' or 'worker'"
  exit 2
fi
