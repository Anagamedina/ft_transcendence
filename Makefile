COMPOSE     := docker compose
COMPOSE_DEV := docker compose -f compose.yaml -f compose.dev.yaml
CERTS_DIR   := gateway/certs
ALEMBIC     := $(COMPOSE) run --rm --no-deps --user "$$(id -u):$$(id -g)" \
	-v $(CURDIR)/backend/app:/app/app:ro \
	-v $(CURDIR)/backend/migrations:/app/migrations \
	--entrypoint alembic
# Same idea as ALEMBIC: runs the seed from the working tree, not the one baked
# into the image, so editing seed_demo.py does not need a rebuild.
SEED        := $(COMPOSE) run --rm --no-deps \
	-v $(CURDIR)/backend/app:/app/app:ro \
	-v $(CURDIR)/backend/seeds:/app/seeds:ro \
	--entrypoint python backend -m seeds.seed_demo

.PHONY: all env check-sim-env certs up dev sim demo seed migrate migration migration-check down build logs ps clean fclean re smoke

all: up

env:
	@test -f .env || cp .env.example .env

# The demo needs the sensor list of .env.example: an older .env leaves the
# new sensors without simulated readings, so they show as offline.
check-sim-env: env
	@grep -qxF "$$(grep '^SIMULATOR_SENSOR_IDS=' .env.example)" .env || \
		echo "WARNING: SIMULATOR_SENSOR_IDS in .env differs from .env.example; copy that line or some demo sensors will show as offline."

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
demo: env certs check-sim-env
	$(COMPOSE) up --build -d --wait
	$(MAKE) seed
	$(COMPOSE) --profile sim up --build -d --wait simulator
	@sh scripts/smoke.sh
	@$(COMPOSE) --profile sim ps

# The seed needs the schema at head; migrating first is a no-op when it is.
seed: migrate
	$(SEED)

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
