#!/usr/bin/env bash
set -euo pipefail

CERTS_DIR="certs"
PRIVATE_KEY_PATH="${CERTS_DIR}/jwt_private.pem"
PUBLIC_KEY_PATH="${CERTS_DIR}/jwt_public.pem"

mkdir -p "$CERTS_DIR"

if [ -f "$PRIVATE_KEY_PATH" ] || [ -f "$PUBLIC_KEY_PATH" ]; then
  echo "JWT ключи уже существуют."
  echo "Если вы хотите сгенерировать новые ключи, сначала удалите существующие:"
  echo "  rm -f $PRIVATE_KEY_PATH $PUBLIC_KEY_PATH"
  exit 1
fi

openssl genpkey \
  -algorithm RSA \
  -out "$PRIVATE_KEY_PATH" \
  -pkeyopt rsa_keygen_bits:2048

openssl rsa \
  -pubout \
  -in "$PRIVATE_KEY_PATH" \
  -out "$PUBLIC_KEY_PATH"

chmod 600 "$PRIVATE_KEY_PATH"
chmod 644 "$PUBLIC_KEY_PATH"

echo "JWT ключи сгенерированы:"
echo "  private: $PRIVATE_KEY_PATH"
echo "  public:  $PUBLIC_KEY_PATH"