#!/bin/sh
set -e

# Entrypoint script to collect static files and run migrations
echo "[[[...entrypoint.sh started...]]]"

# Collect static files and apply database migrations
if [ "${SKIP_COLLECTSTATIC:-0}" = "1" ]; then
  echo "Skipping collectstatic (SKIP_COLLECTSTATIC=1)"
else
  echo "Running collectstatic..."
  # Use the --noinput flag to avoid interactive prompts
  python manage.py collectstatic --noinput
fi
echo "Static files collected."

# Apply database migrations
if [ "${SKIP_MIGRATE:-0}" = "1" ]; then
  echo "Skipping migrate (SKIP_MIGRATE=1)"
else
  echo "Running migrate..."
  python manage.py migrate --noinput
fi
echo "Database migrations applied."

# Execute the command passed as arguments to the script
echo "Final command: $@" 
exec "$@"
echo "[[[...entrypoint.sh finished...]]]"
