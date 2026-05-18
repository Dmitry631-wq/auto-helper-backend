web: python manage.py check && python manage.py migrate --run-syncdb && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
