web: python manage.py migrate --run-syncdb && python manage.py check --deploy 2>&1 || true && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --log-level debug
