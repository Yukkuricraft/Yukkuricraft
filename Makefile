SHELL=/bin/bash

.PHONY: __pre_ensure
__pre_ensure: __ensure_env
__pre_ensure: __ensure_valid_env

.PHONY: __ensure_env
__ensure_env:
ifndef ENV
	@echo 'Must pass ENV: make ENV=(prod|dev1) <target>'
	@echo ''
	@exit 1
endif

.PHONY: __ensure_valid_env
__ensure_valid_env:
	@if ! [[ "$(ENV_STR)" =~ ^(dev|prod)$$ ]]; then echo "ENV value must be 'prod', 'dev', or 'dev#' where # is any int. Got: $(ENV_STR)"; echo ''; exit 1;  fi
	echo "else ifeq ($(strip $(ENV_STR)),dev)"

# Stripping numbers so we only keep dev or prod
ENV_STR=$(shell val='$(ENV)'; echo "$${val//[0-9]/}")
COMPOSE_FILE="docker-compose.$(ENV_STR).yml"
YC_CONTAINER=YC-$(ENV)

.PHONY: up
up: __pre_ensure
up:
	echo $(ENV_STR)
	echo $(COMPOSE_FILE)
	echo $(YC_CONTAINER)
	docker-compose -f $(COMPOSE_FILE) \
		--project-name $(ENV) \
		--env-file env/$(ENV).env \
		up -d

.PHONY: _down
down: __pre_ensure
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
logs: __pre_ensure
logs:
	docker-compose -f $(COMPOSE_FILE) \
		--project-name $(ENV) \
		logs --follow

.PHONY: attach
attach: __pre_ensure
attach:
	docker-compose attach $(YC_CONTAINER)

.PHONY: exec
exec: __pre_ensure
exec:
	echo $(YC_CONTAINER)
	docker exec -it $(YC_CONTAINER) /bin/bash


.PHONY: build
build:
	docker build -f images/minecraft-server/Dockerfile \
		--tag='yukkuricraft/minecraft-server' \
		.
