# Docker
.PHONY: build up up-d down restart logs ps

# Django
.PHONY: bash shell migrate makemigrations createsuperuser demo

# Quality
.PHONY: tests check

# JWT
.PHONY: keys verify-keys

# Docs
.PHONY: schema

# Bruno
.PHONY: bruno bruno-auth bruno-content bruno-security

# Cleanup
.PHONY: clean


build:
	docker compose build

up:
	docker compose up

up-d:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d --build

logs:
	docker compose logs -f app

ps:
	docker compose ps

bash:
	docker compose exec app bash

shell:
	docker compose exec app python manage.py shell

migrate:
	docker compose exec app python manage.py migrate

makemigrations:
	docker compose exec app python manage.py makemigrations

createsuperuser:
	docker compose exec app python manage.py createsuperuser

demo:
	docker compose exec app python manage.py init_demo_data

tests:
	docker compose exec app pytest apps

check:
	docker compose exec app python manage.py check

keys:
	./scripts/generate_jwt_keys.sh

verify-keys:
	./scripts/verify_jwt_keys.sh

clean:
	docker compose down -v

schema:
	docker compose exec app python manage.py spectacular --file schema.yml

bruno:
	cd bruno/JWTGuard && bru run --env local

bruno-auth:
	cd bruno/JWTGuard && bru run Auth --env local

bruno-content:
	cd bruno/JWTGuard && bru run Content --env local

bruno-security:
	cd bruno/JWTGuard && bru run Security --env local