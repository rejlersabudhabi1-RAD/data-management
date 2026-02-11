# Procfile for Railway/Heroku deployment
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
release: python manage.py migrate --noinput
