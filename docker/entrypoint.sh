#!/usr/bin/env bash
set -e

echo "Старт DjangoJWT контейнера..."

if [ ! -f "$JWT_PRIVATE_KEY_PATH" ]; then
  echo "ERROR: Приватный JWT ключ не найден: $JWT_PRIVATE_KEY_PATH"
  echo "Генерация ключей:"
  echo "  mkdir -p certs"
  echo "  openssl genpkey -algorithm RSA -out certs/jwt_private.pem -pkeyopt rsa_keygen_bits:2048"
  echo "  openssl rsa -pubout -in certs/jwt_private.pem -out certs/jwt_public.pem"
  exit 1
fi

if [ ! -f "$JWT_PUBLIC_KEY_PATH" ]; then
  echo "ERROR: Публичный JWT ключ не найден: $JWT_PUBLIC_KEY_PATH"
  exit 1
fi

exec "$@"