#!/usr/bin/env bash
set -euo pipefail

PRIVATE_KEY_PATH="certs/jwt_private.pem"
PUBLIC_KEY_PATH="certs/jwt_public.pem"
TMP_PUBLIC_KEY="/tmp/djangojwt_public_from_private.pem"

if [ ! -f "$PRIVATE_KEY_PATH" ]; then
  echo "Приватный ключ не найден: $PRIVATE_KEY_PATH"
  exit 1
fi

if [ ! -f "$PUBLIC_KEY_PATH" ]; then
  echo "Публичный ключ не найден: $PUBLIC_KEY_PATH"
  exit 1
fi

openssl rsa \
  -in "$PRIVATE_KEY_PATH" \
  -pubout \
  -outform PEM \
  > "$TMP_PUBLIC_KEY"

if diff -q "$TMP_PUBLIC_KEY" "$PUBLIC_KEY_PATH" > /dev/null; then
  echo "Пара JWT ключей валидна."
else
  echo "Пара JWT ключей недействительна: открытый ключ не совпадает с закрытым ключом."
  exit 1
fi