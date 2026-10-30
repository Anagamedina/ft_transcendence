COMPOSE     := docker compose
COMPOSE_DEV := docker compose -f compose.yaml -f compose.dev.yaml
CERTS_DIR   := gateway/certs
# npm writes this file on every install: it marks node_modules as up to date
# with its lockfile, so `npm ci` only runs again when the lockfile changes.
FRONTEND_DEPS := frontend/node_modules/.package-lock.json
E2E_DEPS      := e2e/node_modules/.package-lock.json
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

# Full local bootstrap. It is safe to repeat: demo data is loaded only into
# an empty database, while all named volumes survive `make down`.
# Step by step: make each prerequisite, then each line below, in order.
# `make -n all` prints the commands without running them.
all: env certs config-check check-sim-env
	$(COMPOSE) up --build -d --wait --wait-timeout 120 database backend gateway mailpit
	$(MAKE) seed-if-empty
	$(COMPOSE) up --build -d --wait --wait-timeout 120 backup
	$(COMPOSE) --profile sim up --build -d --wait --wait-timeout 120 simulator
	$(MAKE) storage-check
	$(MAKE) smoke
	@$(COMPOSE) --profile sim ps

setup:
	@sh scripts/setup.sh

# Never overwrites an existing .env. A new one gets random keys instead of the
# example ones, so a clean clone does not run with secrets published in the repo.
env:
	@test -f .env || sed \
		-e "s|^SECRET_KEY=.*|SECRET_KEY=$$(openssl rand -hex 32)|" \
		-e "s|^INGEST_API_KEY=.*|INGEST_API_KEY=$$(openssl rand -hex 32)|" \
		-e "s|^PUBLIC_API_KEY=.*|PUBLIC_API_KEY=$$(openssl rand -hex 32)|" \
		-e "s|^PUBLIC_API_WRITE_KEY=.*|PUBLIC_API_WRITE_KEY=$$(openssl rand -hex 32)|" \
		.env.example > .env

config-check: env
	@sh scripts/validate_env.sh

doctor:
	@sh scripts/doctor.sh

# The demo needs the sensor list and per-sensor scenarios of .env.example.
# `make all` promises a complete demo, so an old local .env must fail instead
# of silently starting a simulator that cannot populate the seeded sensors.
check-sim-env: env
	@for var in SIMULATOR_SENSOR_IDS SIMULATOR_SCENARIOS; do \
		expected="$$(grep "^$$var=" .env.example)"; \
		actual="$$(grep "^$$var=" .env || true)"; \
		[ "$$actual" = "$$expected" ] || { \
			echo "config-check: FAIL  $$var in .env must match .env.example for make all" >&2; \
			echo "  expected: $$expected" >&2; \
			echo "  update .env or use make up for infrastructure without the demo" >&2; \
			exit 1; \
		}; \
	done

certs:
	@mkdir -p $(CERTS_DIR)
	@if test -f $(CERTS_DIR)/aquaguard.crt && test -f $(CERTS_DIR)/aquaguard.key; then \
		echo "certs: existing certificate pair"; \
	elif test -e $(CERTS_DIR)/aquaguard.crt || test -e $(CERTS_DIR)/aquaguard.key; then \
		echo "certs: incomplete certificate pair; refusing to overwrite it" >&2; exit 1; \
	else \
		openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
			-keyout $(CERTS_DIR)/aquaguard.key \
			-out $(CERTS_DIR)/aquaguard.crt \
			-subj "/C=ES/O=AquaGuard/CN=localhost" \
			-addext "subjectAltName=DNS:localhost,IP:127.0.0.1"; \
	fi

up: env certs config-check
	$(COMPOSE) up --build -d --wait --wait-timeout 120
	@$(COMPOSE) ps

dev-infra: env certs config-check
	$(COMPOSE_DEV) up --build -d
	@$(COMPOSE_DEV) ps

frontend-install: $(FRONTEND_DEPS)

$(FRONTEND_DEPS): frontend/package-lock.json
	npm --prefix frontend ci --no-audit --no-fund

e2e-install: $(E2E_DEPS)

$(E2E_DEPS): e2e/package-lock.json
	npm --prefix e2e ci --no-audit --no-fund
	npx --prefix e2e playwright install chromium firefox webkit

frontend-dev: env certs $(FRONTEND_DEPS)
	npm --prefix frontend run dev -- --host localhost

dev: dev-infra
	@$(MAKE) frontend-dev

# Starts the simulator against a seeded database, so its sensors exist.
sim: env certs config-check check-sim-env
	$(COMPOSE) up --build -d --wait --wait-timeout 120 database backend gateway mailpit
	$(MAKE) seed-if-empty
	$(COMPOSE) up --build -d --wait --wait-timeout 120 backup
	$(COMPOSE) --profile sim up --build -d --wait --wait-timeout 120 simulator
	@$(COMPOSE) --profile sim ps

# Kept as a readable alias for evaluators and existing documentation.
demo: all

# The seed needs the schema at head; migrating first is a no-op when it is.
seed: migrate
	$(SEED)

# #275: one alert in each phase of the client notices, with times from now.
# Run it again to refresh the phases.
seed-avisos: migrate
	$(COMPOSE) run --rm --no-deps \
		-v $(CURDIR)/backend/app:/app/app:ro \
		-v $(CURDIR)/backend/seeds:/app/seeds:ro \
		--entrypoint python backend -m seeds.seed_avisos

# Never overwrite a working database during a normal `make all`. The explicit
# `make seed` target remains available when the demo needs to be refreshed.
seed-if-empty:
	@sh scripts/bootstrap_seed.sh

# ALEMBIC uses `run --no-deps`, so the database has to be up first.
migrate: env
	$(COMPOSE) up -d --wait database
	$(ALEMBIC) backend upgrade head

migration:
	@test -n "$(MSG)" || { echo 'Usage: make migration MSG="description"'; exit 1; }
	$(ALEMBIC) backend revision --autogenerate -m "$(MSG)"

migration-check:
	@sh scripts/migration_check.sh

storage-check:
	@sh scripts/storage_check.sh

test-backend: env
	$(COMPOSE) up -d --wait database
	$(COMPOSE) run --rm --no-deps -v $(CURDIR)/backend:/src:ro --entrypoint sh backend -c 'cd /src && python -m pytest -q -p no:cacheprovider tests'

test-frontend: $(FRONTEND_DEPS)
	npm --prefix frontend test -- --run

# The E2E tests drive the running stack through the gateway. They log in and
# register many times in a few seconds, so the gateway runs with a high rate
# limit during the suite and is put back with the normal one afterwards.
test-e2e: $(E2E_DEPS)
	@curl -skf https://localhost/api/health >/dev/null || \
		{ echo "test-e2e: the stack is not running. Start it with: make all" >&2; exit 1; }
	PUBLIC_RATE_LIMIT=1000r/m $(COMPOSE) up -d --no-deps --wait gateway
	@status=0; npm --prefix e2e test || status=$$?; \
		$(COMPOSE) up -d --no-deps --wait gateway; \
		exit $$status

lint: $(FRONTEND_DEPS)
	npm --prefix frontend run lint

format: $(FRONTEND_DEPS)
	npm --prefix frontend run format

compose-check: env
	$(COMPOSE) config --quiet

check: compose-check lint test-frontend

smoke:
	@sh scripts/smoke.sh

backup:
	$(COMPOSE) exec -T backup backup.sh

backups:
	@$(COMPOSE) exec -T backup sh -c 'ls -lh /backups | tail -n +2'

restore:
	@sh scripts/restore.sh "$(FILE)"

# Restores a backup into a temporary database and compares it with the real
# one. Without FILE it makes a new backup first; see docs/disaster-recovery.md.
backup-verify:
	@bash scripts/backup_verify.sh "$(FILE)"

down:
	$(COMPOSE) --profile sim down --remove-orphans

build: env
	$(COMPOSE) --profile sim build

logs:
	$(COMPOSE) --profile sim logs -f

ps:
	$(COMPOSE) ps

# clean removes the project images; fclean also removes the volumes.
clean:
	$(COMPOSE) --profile sim down --rmi local --remove-orphans

fclean:
	$(COMPOSE) --profile sim down -v --rmi local --remove-orphans

# Sequential on purpose: with `make -j`, prerequisites would run in parallel
# and fclean could delete volumes while all is starting the stack.
re:
	$(MAKE) fclean
	$(MAKE) all

.PHONY: all setup env config-check doctor check-sim-env certs up dev dev-infra frontend-install e2e-install frontend-dev sim demo seed seed-avisos seed-if-empty migrate migration migration-check storage-check test-backend test-frontend test-e2e lint format compose-check check down build logs ps clean fclean re smoke backup backups restore backup-verify
