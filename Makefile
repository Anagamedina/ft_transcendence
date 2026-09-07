COMPOSE := docker compose

.PHONY: all env up down build logs ps clean fclean re

all: up

env:
	@test -f .env || cp .env.example .env

up: env
	$(COMPOSE) up --build -d
	@$(COMPOSE) ps

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
