COMPOSE_FILE=docker-compose.yml
YC_CONTAINER=Yukkuricraft

.PHONY: up
up:
	docker-compose -f $(COMPOSE_FILE) up -d

.PHONY: down
down:
	docker-compose -f $(COMPOSE_FILE) down

.PHONY: restart
restart: down up

.PHONY: logs
logs:
	docker-compose -f $(COMPOSE_FILE) logs --follow

.PHONY: attach
attach:
	docker-compose attach $(YC_CONTAINER)
