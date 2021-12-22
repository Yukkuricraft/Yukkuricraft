.PHONY: __ensure_env
__ensure_env:
ifndef ENV
	@echo ''
	@echo 'Must pass ENV: make ENV=(prod|dev1) <target>'
	@echo ''
	@exit 1
endif

COMPOSE_FILE=docker-compose.yml
YC_CONTAINER=YC-$(ENV)

.PHONY: up
up: __ensure_env
up:
	docker-compose -f $(COMPOSE_FILE) \
		--project-name $(ENV) \
		--env-file env/$(ENV).env \
		up -d

.PHONY: _down
down: __ensure_env
down:
	docker-compose -f $(COMPOSE_FILE) \
		--project-name $(ENV) \
		--env-file env/$(ENV).env \
		down

.PHONY: clean
clean:
	docker volume prune -f

.PHONY: restart
restart: down up

.PHONY: cleanstart
cleanstart: down clean up

.PHONY: logs
logs: __ensure_env
logs:
	docker-compose -f $(COMPOSE_FILE) \
		--project-name $(ENV) \
		logs --follow

.PHONY: attach
attach: __ensure_env
attach:
	docker-compose attach $(YC_CONTAINER)

.PHONY: exec
exec: __ensure_env
exec:
	echo $(YC_CONTAINER)
	docker exec -it $(YC_CONTAINER) /bin/bash


.PHONY: build
build:
	docker build -f images/minecraft-server/Dockerfile \
		--tag='yukkuricraft/minecraft-server' \
		.
