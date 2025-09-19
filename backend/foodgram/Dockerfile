FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=foodgram.settings

WORKDIR /app

# Сначала зависимости — чтобы кэшировались
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y gcc \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# Затем ВЕСЬ проект
COPY . .

# Собираем статику во время билда образа
RUN python manage.py collectstatic --noinput

# (опционально) миграции можно запускать при старте контейнера, а не на билде
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]