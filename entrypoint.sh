#!/bin/sh
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# dev server – swap for gunicorn in real prod deployments
python manage.py runserver 0.0.0.0:8001
