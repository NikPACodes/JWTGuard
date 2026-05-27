#!/usr/bin/env bash
set -euo pipefail

echo "Старт DjangoJWT контейнера..."

if [ -z "${JWT_PRIVATE_KEY_PATH:-}" ]; then
  echo "ERROR: Приватный ключ JWT_PRIVATE_KEY_PATH не задан."
  exit 1
fi

if [ -z "${JWT_PUBLIC_KEY_PATH:-}" ]; then
  echo "Публичный ключ JWT_PUBLIC_KEY_PATH не задан."
  exit 1
fi

if [ ! -f "$JWT_PRIVATE_KEY_PATH" ]; then
  echo "ERROR: Приватный JWT ключ не найден: $JWT_PRIVATE_KEY_PATH"
  echo ""
  echo "Сгенерируйте JWT ключ перед стартом приложения:"
  echo "  ./scripts/generate_jwt_keys.sh"
  echo ""
  echo "Проверьте верификацию ключа:"
  echo "  ./scripts/verify_jwt_keys.sh"
  exit 1
fi

if [ ! -f "$JWT_PUBLIC_KEY_PATH" ]; then
  echo "ERROR: JWT public key not found: $JWT_PUBLIC_KEY_PATH"
  echo ""
  echo "Сгенерируйте JWT ключ перед стартом приложения:"
  echo "  ./scripts/generate_jwt_keys.sh"
  echo ""
  echo "Проверьте верификацию ключа:"
  echo "  ./scripts/verify_jwt_keys.sh"
  exit 1
fi

python /app/docker/wait_for_services.py

echo "DjangoJWT контейнер готов. Выполняется команда: $*"

exec "$@"