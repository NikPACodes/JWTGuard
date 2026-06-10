# Copyright 2026 Nikolay Petukhov (NikPACodes)
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.
import os
import socket
import time
from urllib.parse import urlparse


def wait_for_tcp(host: str, port: int, service_name: str, timeout: int = 30) -> None:
    started_at = time.monotonic()

    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"{service_name} доступен по адресу {host}:{port}")
                return
        except OSError:
            if time.monotonic() - started_at > timeout:
                raise TimeoutError(
                    f"Истекло время ожидания {service_name} на {host}:{port}"
                )

            print(f"Ожидание {service_name} на {host}:{port}...")
            time.sleep(1)


def main() -> None:
    postgres_host = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

    parsed_redis_url = urlparse(redis_url)

    redis_host = parsed_redis_url.hostname or "redis"
    redis_port = parsed_redis_url.port or 6379

    wait_for_tcp(postgres_host, postgres_port, "PostgreSQL")
    wait_for_tcp(redis_host, redis_port, "Redis")


if __name__ == "__main__":
    main()