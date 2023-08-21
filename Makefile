###########
## SETUP ##
###########
SHELL=/bin/bash
ENV?=dev1
DOCKER_GID=$(shell getent group docker | cut -d: -f3)

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
	@if ! [[ -f "gen/$(ENV).env" ]]; then \
		echo "Got '$(ENV)' for ENV but could not find 'gen/$(ENV).env'! Was ./generate-env-file run first? Aborting."; \
		echo ''; \
		exit 1; \
	fi

#############
## TARGETS ##
#############
# ENV_TYPE strips numbers so we only keep dev or prod
ENV_TYPE=$(shell val='$(ENV)'; echo "$${val//[0-9]/}")

COMPOSE_FILE="gen/docker-compose-$(ENV).yml"
WEB_COMPOSE_FILE="docker-compose.web.yml"

YC_CONTAINER=$(ENV)_mc_survival_1 # This needs to be refactored to hit all containers...
YC_FS_ROOT?=/var/lib/yukkuricraft

ARGS=$(filter-out $@,$(MAKECMDGOALS))

COMPOSE_ARGS=--project-name $(ENV) \
			 --project-directory $(shell pwd) \
			 --env-file gen/$(ENV).env

COPY_PROD_WORLD?=
COPY_PROD_PLUGINS?=
PRE=ENV=$(ENV) ENV_TYPE=$(ENV_TYPE) COPY_PROD_WORLD=$(COPY_PROD_WORLD) COPY_PROD_PLUGINS=$(COPY_PROD_PLUGINS)

.PHONY: save_devdata_to_disk
save_devdata_to_disk: __pre_ensure
save_devdata_to_disk:
	@if [[ "$(ENV_TYPE)" == "prod" ]]; then \
		echo "You ran the 'save_devdata_to_disk' target with an ENV_TYPE of prod! Aborting."; \
		exit 1; \
	fi
	@if [[ ! -d "${YC_FS_ROOT}/env/${ENV}/worlds" ]]; then \
		echo "Please create the '${YC_FS_ROOT}/${ENV}/worlds' directory owned by minecraft:minecraft to continue. Aborting"; \
		exit 1; \
	elif [[ ! -d "${YC_FS_ROOT}/env/${ENV}/plugins" ]]; then \
		echo "Please create the '${YC_FS_ROOT}/${ENV}/plugins' directory owned by minecraft:minecraft to continue. Aborting"; \
		exit 1; \
	fi
	@docker run \
		--rm \
		--mount type=bind,source=${YC_FS_ROOT}/env/${ENV}/worlds,target=/worlds-data \
		--mount type=bind,source=${YC_FS_ROOT}/env/${ENV}/plugins,target=/plugins-data \
		--volume $(PWD)/scripts/rsync.sh:/rsync.sh \
		--volumes-from YC-${ENV} \
		eeacms/rsync \
		/rsync.sh

.PHONY: save_world
save_world:
	-echo 'save-all' | socat EXEC:"docker attach $(YC_CONTAINER)",pty STDIN

.PHONY: run_cmd_on_container
run_cmd_on_container:
	# TODO: This should prob be made more robust with python eventually
	-echo '$(word 1,$(ARGS))' | socat EXEC:"docker attach $(word 2,$(ARGS))",pty STDIN

# It's 'make generate' but it's more 'make generate_runtime_configs_for_envs'
.PHONY: generate
generate: generate_velocity_config
generate: generate_env_file
generate: generate_docker_compose

.PHONY: generate_velocity_config
generate_velocity_config:
	$(PRE) ./generate-velocity-config

.PHONY: generate_env_file
generate_env_file:
	$(PRE) ./generate-env-file

.PHONY: generate_docker_compose
generate_docker_compose:
	$(PRE) ./generate-docker-compose

# DEV ENV CREATE/DELETE

.PHONY: create_new_env
create_new_env:
	# Do we want to do based on current active env or always use prod as BASE_ENV?
	BASE_ENV=prod \
	NEW_ENV=$(word 1,$(ARGS)) \
	VELOCITY_PORT=$(word 2,$(ARGS)) \
	ENV_ALIAS=$(word 3,$(ARGS)) \
	./generate-new-dev-env
	ENV=$(word 1,$(ARGS)) ./generate-docker-compose
	ENV=$(word 1,$(ARGS)) ./generate-velocity-config

.PHONY: chownmod_container_logs
chownmod_container_logs:
	sudo chown -R minecraft:minecraft container_logs
	sudo chmod -R 775 container_logs

.PHONY: test
test:
	echo $(word 2,$(ARGS))

.PHONY: delete_env
delete_env:
	ENV=$(ARGS) ./scripts/delete_dev_env.sh

# BUILD

.PHONY: build
build: build_minecraft_server
build: build_api

.PHONY: build_minecraft_server
build_minecraft_server:
	docker build -f images/minecraft-server/Dockerfile \
		--no-cache \
		--tag='yukkuricraft/minecraft-server' \
		.

.PHONY: build_api
build_api:
	docker build -f images/yc-docker-api/Dockerfile \
		--build-arg DOCKER_GID=${DOCKER_GID} \
		--tag='yukkuricraft/yc-docker-api' \
		.

# UP DOWN RESTARTS

.PHONY: up_web
up_web: ENV=prod
up_web:
	docker compose -f $(WEB_COMPOSE_FILE) \
		--env-file=gen/$(ENV).env \
		up \
		-d

.PHONY: down_web
down_web:
	docker compose -f docker-compose.web.yml down

.PHONY: restart_web
restart_web:
	docker compose -f docker-compose.web.yml restart

.PHONY: up
up: generate
up: __pre_ensure
up:
	$(PRE) docker compose -f $(COMPOSE_FILE) \
		$(COMPOSE_ARGS) \
		up -d

.PHONY: up_one
up_one: generate
up_one: __pre_ensure
up_one:
	$(PRE) docker compose -f $(COMPOSE_FILE) \
		$(COMPOSE_ARGS) \
		up \
		-d \
		$(ARGS)

.PHONY: down
down: __pre_ensure
down: save_world
down:
	$(PRE) docker compose -f $(COMPOSE_FILE) \
		$(COMPOSE_ARGS) \
		down

.PHONY: restart
restart: generate
restart: __pre_ensure
restart:
	$(PRE) docker compose -f $(COMPOSE_FILE) \
		$(COMPOSE_ARGS) \
		restart

.PHONY: restart_one
restart_one: generate
restart_one: __pre_ensure
restart_one:
	$(PRE) docker compose -f $(COMPOSE_FILE) \
		$(COMPOSE_ARGS) \
		restart \
		$(ARGS)

# COMPOUNDS

.PHONY: purge
purge:
	docker volume prune -f

.PHONY: restart_velocity
restart_velocity:
	docker restart Velocity-$(ENV)

.PHONY: purgestart
purgestart: down purge up

# HELPERS

.PHONY: logs
logs: __pre_ensure
logs:
	$(PRE) docker compose -f $(COMPOSE_FILE) \
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
