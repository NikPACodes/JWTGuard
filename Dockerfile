FROM python:3.12-slim

# Запрещаем Python создавать .pyc файлы (__pycache__).
ENV PYTHONDONTWRITEBYTECODE=1
# Отключае буферизацию stdout/stderr.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# build-essential: Набор build tools для C расширений (psycopg2, cryptography).
# libpq-dev:       Набор для PostgreSQL (psycopg2).
# netcat-openbsd:  Утилита nc для проверки доступности TCP-портов. (entrypoint.sh)
# openssl:         Утилита для SSL/TLS и криптографии (RS256).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       netcat-openbsd \
       openssl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN pip install --upgrate pip \
    && pip install ".[dev]"

COPY . .

RUN chmod +x /app/docker/entrypoint.sh

ENTRYPOINT ["/app/docker/entrypoint.sh"]