###########
## SETUP ##
###########
SHELL=/bin/bash
ENV?=dev1

.PHONY: __pre_ensure
__pre_ensure: __ensure_env
__pre_ensure: __ensure_valid_env
__pre_ensure: __ensure_env_file_exists

.PHONY: __ensure_env
__ensure_env:
	@if [[ -z "$(ENV)" ]]; then \
		echo 'Must pass ENV: make ENV=(prod|dev1) <target>. Aborting.'; \
		echo ''; \
		exit 1; \
	fi

.PHONY: __ensure_valid_env
__ensure_valid_env:
	@if ! [[ "$(ENV_TYPE)" =~ ^(dev|prod)$$ ]]; then \
		echo "ENV value must be 'prod', 'dev', or 'dev#' where # is any int. Got: $(ENV_TYPE). Aborting."; \
		echo ''; \
		exit 1; \
	fi

.PHONY: __ensure_env_file_exists
__ensure_env_file_exists:
	@if ! [[ -f "env/$(ENV).env" ]]; then \
		echo "Got '$(ENV)' for ENV but could not find 'env/$(ENV).env'! Aborting."; \
		echo ''; \
		exit 1; \
	fi

#############
## TARGETS ##
#############
# ENV_TYPE strips numbers so we only keep dev or prod
ENV_TYPE=$(shell val='$(ENV)'; echo "$${val//[0-9]/}")
COMPOSE_FILE="docker-compose.yml"
YC_CONTAINER=YC-$(ENV)
YC_ROOT?=/var/lib/yukkuricraft

COMPOSE_ARGS=--project-name $(ENV) \
			 --env-file env/$(ENV).env

COPY_PROD_WORLD?=
PRE=ENV_TYPE=$(ENV_TYPE) COPY_PROD_WORLD=$(COPY_PROD_WORLD)

.PHONY: save_devdata_to_disk
save_devdata_to_disk: __pre_ensure
save_devdata_to_disk:
	@if [[ "$(ENV_TYPE)" == "prod" ]]; then \
		echo "You ran the 'save_devdata_to_disk' target with an ENV_TYPE of prod! Aborting."; \
		exit 1; \
	fi
	@if [[ ! -d "${YC_ROOT}/${ENV}/worlds" ]]; then \
		echo "Please create the '${YC_ROOT}/${ENV}/worlds' directory owned by minecraft:minecraft to continue. Aborting"; \
		exit 1; \
	elif [[ ! -d "${YC_ROOT}/${ENV}/plugins" ]]; then \
		echo "Please create the '${YC_ROOT}/${ENV}/plugins' directory owned by minecraft:minecraft to continue. Aborting"; \
		exit 1; \
	fi
	@docker run \
		--rm \
		--mount type=bind,source=${YC_ROOT}/${ENV}/worlds,target=/worlds-data \
		--mount type=bind,source=${YC_ROOT}/${ENV}/plugins,target=/plugins-data \
		--volume $(PWD)/scripts/rsync.sh:/rsync.sh \
		--volumes-from YC-${ENV} \
		eeacms/rsync \
		/rsync.sh

.PHONY: save_world
save_world:
	-echo 'save-all' | socat EXEC:"docker attach $(YC_CONTAINER)",pty STDIN

.PHONY: build
build:
	docker build -f images/minecraft-server/Dockerfile \
		--tag='yukkuricraft/minecraft-server' \
		.

.PHONY: up
up: __pre_ensure
up:
	$(PRE) docker-compose -f $(COMPOSE_FILE) \
		$(COMPOSE_ARGS) \
		up -d

.PHONY: _down
down: __pre_ensure
down: save_world
down:
	$(PRE) docker-compose -f $(COMPOSE_FILE) \
		$(COMPOSE_ARGS) \
		down

.PHONY: purge
purge:
	docker volume prune -f

.PHONY: restart
restart: down up

.PHONY: purgestart
purgestart: down purge up

.PHONY: logs
logs: __pre_ensure
logs:
	$(PRE) docker-compose -f $(COMPOSE_FILE) \
		$(COMPOSE_ARGS) \
		logs --follow

.PHONY: attach
attach: __pre_ensure
attach:
	$(PRE) docker attach --sig-proxy=false $(YC_CONTAINER)

.PHONY: exec
exec: __pre_ensure
exec:
	docker exec -it $(YC_CONTAINER) /bin/bash

# Prod Shortcuts
.PHONY: up_prod
up_prod: ENV=prod
up_prod: up

.PHONY: down_prod
down_prod: ENV=prod
down_prod: down

.PHONY: logs_prod
logs_prod: ENV=prod
logs_prod: logs

.PHONY: exec_prod
exec_prod: ENV=prod
exec_prod: exec

.PHONY: attach_prod
attach_prod: ENV=prod
attach_prod: attach

.PHONY: save_world_prod
save_world_prod: ENV=prod
save_world_prod: save_world
