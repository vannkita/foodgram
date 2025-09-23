FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=foodgram.settings

WORKDIR /app


COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc curl \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y gcc \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]