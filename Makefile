COMPOSE     := docker compose
COMPOSE_DEV := docker compose -f compose.yaml -f compose.dev.yaml
CERTS_DIR   := gateway/certs

.PHONY: all env certs up dev down build logs ps clean fclean re

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

down:
	$(COMPOSE) down

build: env
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

clean:
	$(COMPOSE) down --remove-orphans

fclean:
	$(COMPOSE) down -v --remove-orphans

re: fclean up
