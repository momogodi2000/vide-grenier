# Dockerfile for Django production (Gunicorn)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY vide/requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY vide /app/

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "vide.wsgi:application", "--bind", "0.0.0.0:8000"]
