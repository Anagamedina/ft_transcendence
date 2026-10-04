COMPOSE     := docker compose
COMPOSE_DEV := docker compose -f compose.yaml -f compose.dev.yaml
CERTS_DIR   := gateway/certs
ALEMBIC     := $(COMPOSE) run --rm --no-deps --user "$$(id -u):$$(id -g)" \
	-v $(CURDIR)/backend/app:/app/app:ro \
	-v $(CURDIR)/backend/migrations:/app/migrations \
	--entrypoint alembic

.PHONY: all env certs up dev sim demo seed migrate migration migration-check down build logs ps clean fclean re smoke

all: up

env:
	@test -f .env || cp .env.example .env

certs:
	@mkdir -p $(CERTS_DIR)
	@test -f $(CERTS_DIR)/aquaguard.crt && test -f $(CERTS_DIR)/aquaguard.key || \
		openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
			-keyout $(CERTS_DIR)/aquaguard.key \
			-out $(CERTS_DIR)/aquaguard.crt \
			-subj "/C=ES/O=AquaGuard/CN=localhost" \
			-addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

up: env certs
	$(COMPOSE) up --build -d
	@$(COMPOSE) ps

dev: env certs
	$(COMPOSE_DEV) up --build -d
	@$(COMPOSE_DEV) ps

sim: env certs
	$(COMPOSE) --profile sim up --build -d
	@$(COMPOSE) --profile sim ps

# Whole project in one command: stack, demo data, simulator, then the smoke test.
demo: env certs
	$(COMPOSE) up --build -d --wait
	$(MAKE) seed
	$(COMPOSE) --profile sim up --build -d --wait simulator
	@sh scripts/smoke.sh
	@$(COMPOSE) --profile sim ps

seed:
	$(COMPOSE) exec backend python -m seeds.seed_demo

migrate:
	$(ALEMBIC) backend upgrade head

migration:
	@test -n "$(MSG)" || { echo 'Usage: make migration MSG="description"'; exit 1; }
	$(ALEMBIC) backend revision --autogenerate -m "$(MSG)"

migration-check:
	@sh scripts/migration_check.sh

smoke:
	@sh scripts/smoke.sh

down:
	$(COMPOSE) --profile sim down

build: env
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

clean:
	$(COMPOSE) --profile sim down --remove-orphans

fclean:
	$(COMPOSE) --profile sim down -v --remove-orphans

re: fclean up
