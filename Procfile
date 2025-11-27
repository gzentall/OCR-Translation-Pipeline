# Procfile for Heroku/Railway/Render deployment

web: python3 startup.py && gunicorn app:app --workers 2 --timeout 300 --bind 0.0.0.0:$PORT

