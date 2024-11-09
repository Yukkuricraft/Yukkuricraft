###########
## SETUP ##
###########
SHELL=/bin/bash
ENV?=env2
CURRENT_UID=$(shell id -u)
CURRENT_GID=$(shell id -g)
DOCKER_GID=$(shell python -c 'import os; print(os.stat(os.path.realpath("/var/run/docker.sock")).st_gid)')

.EXPORT_ALL_VARIABLES:
ifeq ($(shell hostname), neo-yukkuricraft)
  export WEB_DOCKER_ENV_FILE=envs/prod.env
  export DOCKER_API_HOST=docker.yukkuricraft.net
  export DOCKER_SOCKET_URI=/tmp/docker.sock
  export WEB_COMPOSE_FILE="docker-compose.web.yml"
else ifeq ($(shell hostname), cirno.localdomain)
  export WEB_DOCKER_ENV_FILE=envs/dev.env
  export DOCKER_API_HOST=dev.docker.yukkuricraft.net
  export DOCKER_SOCKET_URI=/tmp/docker.sock
  export WEB_COMPOSE_FILE="docker-compose.web.yml"
else
  export WEB_DOCKER_ENV_FILE=envs/localhost.env
  export DOCKER_API_HOST=docker.localhost
  ifneq (,$(findstring Darwin,$(shell uname)))
    export WEB_COMPOSE_FILE="docker-compose.web.mac.yml"
    export DOCKER_SOCKET_URI=socat:2375
  else
    export WEB_COMPOSE_FILE="docker-compose.web.yml"
    export DOCKER_SOCKET_URI=/tmp/docker.sock
  endif
endif

.PHONY: __pre_ensure
__pre_ensure: __ensure_env
__pre_ensure: __ensure_valid_env
__pre_ensure: __ensure_env_file_exists

.PHONY: __ensure_env
__ensure_env:
	@if [[ -z "$(ENV)" ]]; then \
		echo 'Must pass ENV: make ENV=(env1|env2|env#) <target>. Aborting.'; \
		echo ''; \
		exit 1; \
	fi

.PHONY: __ensure_valid_env
__ensure_valid_env:
	@if ! [[ "$(ENV)" =~ ^env ]]; then \
		echo "ENV value must be 'env#' where # is any int. Got: $(ENV). Aborting."; \
		echo ''; \
		exit 1; \
	fi

.PHONY: __ensure_env_file_exists
__ensure_env_file_exists:
	@if ! [[ -f "gen/env-files/$(ENV).env" ]]; then \
		echo "Got '$(ENV)' for ENV but could not find 'gen/env-files/$(ENV).env'! Was ./generate-env-file run first? Aborting."; \
		echo ''; \
		exit 1; \
	fi

#############
## TARGETS ##
#############

COMPOSE_FILE="gen/docker-compose/docker-compose-$(ENV).yml"

ARGS=$(filter-out $@,$(MAKECMDGOALS))

COMPOSE_ARGS=--project-name $(ENV) \
			 --project-directory $(shell pwd) \
			 --env-file gen/env-files/$(ENV).env

PRE=ENV=$(ENV)

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
	BASE_ENV=env1 \
	NEW_ENV=$(word 1,$(ARGS)) \
	VELOCITY_PORT=$(word 2,$(ARGS)) \
	ENV_ALIAS=$(word 3,$(ARGS)) \
	./generate-new-dev-env
	ENV=$(word 1,$(ARGS)) ./generate-docker-compose
	ENV=$(word 1,$(ARGS)) ./generate-velocity-config

# BUILD

.PHONY: build
build: build_minecraft_server
build: build_api
build: build_nginx
build: build_mysql_backup
build: build_mc_backup
build: build_mc_proxy
build: build_postgres

.PHONY: build_minecraft_server
build_minecraft_server:
	docker build -f images/minecraft-server/Dockerfile \
		--no-cache \
		--build-arg HOST_UID=${CURRENT_UID} \
		--build-arg HOST_GID=${CURRENT_GID} \
		--build-arg DOCKER_GID=${DOCKER_GID} \
		--tag='yukkuricraft/minecraft-server' \
		.

.PHONY: build_api
build_api:
	docker build -f images/yc-docker-api/Dockerfile \
		--no-cache \
		--build-arg HOST_UID=${CURRENT_UID} \
		--build-arg HOST_GID=${CURRENT_GID} \
		--build-arg DOCKER_GID=${DOCKER_GID} \
		--tag='yukkuricraft/yc-docker-api' \
		.

.PHONY: build_nginx
build_nginx:
	docker build -f images/nginx-proxy/Dockerfile \
		--no-cache \
		--build-arg HOST_UID=${CURRENT_UID} \
		--build-arg HOST_GID=${CURRENT_GID} \
		--build-arg DOCKER_GID=${DOCKER_GID} \
		--build-arg DOCKER_API_HOST=${DOCKER_API_HOST} \
		--build-arg DOCKER_SOCKET_URI=${DOCKER_SOCKET_URI} \
		--tag='yukkuricraft/nginx-proxy' \
		.

.PHONY: build_mc_backup
build_mc_backup:
	docker build -f images/mc-backup-restic/Dockerfile \
		--no-cache \
		--build-arg HOST_UID=${CURRENT_UID} \
		--build-arg HOST_GID=${CURRENT_GID} \
		--tag='yukkuricraft/mc-backup-restic' \
		.

.PHONY: build_postgres
build_postgres:
	docker build -f images/yc-postgres/Dockerfile \
		--no-cache \
		--build-arg HOST_UID=${CURRENT_UID} \
		--build-arg HOST_GID=${CURRENT_GID} \
		--tag='yukkuricraft/postgres' \
		.

.PHONY: build_mc_proxy
build_mc_proxy:
	docker build -f images/yc-mc-proxy/Dockerfile \
		--no-cache \
		--build-arg HOST_UID=${CURRENT_UID} \
		--build-arg HOST_GID=${CURRENT_GID} \
		--tag='yukkuricraft/mc-proxy' \
		.

.PHONY: build_mysql_backup
build_mysql_backup:
	docker build -f images/mysql-backup-restic/Dockerfile \
		--no-cache \
		--build-arg HOST_UID=${CURRENT_UID} \
		--build-arg HOST_GID=${CURRENT_GID} \
		--tag='yukkuricraft/mysql-backup-restic' \
		.

# YC2.0 api/frontend
.PHONY: up_web
up_web: ENV=env1
up_web:
	docker compose -f $(WEB_COMPOSE_FILE) \
		--env-file=${WEB_DOCKER_ENV_FILE} \
		up \
		-d

.PHONY: down_web
down_web:
	docker compose -f $(WEB_COMPOSE_FILE) \
		--env-file=${WEB_DOCKER_ENV_FILE} \
		down

.PHONY: restart_web
restart_web:
	docker compose -f $(WEB_COMPOSE_FILE) \
		--env-file=${WEB_DOCKER_ENV_FILE} \
		restart

# Containerized YC Environments

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

.PHONY: run_entrypoint_target_on_mysql_backup_restic
run_entrypoint_target_on_mysql_backup_restic:
	$(PRE) docker run \
		--env-file=secrets/minecraft_db.env \
		-e DB_SERVER=YC-$(ENV)-mysql \
		-e DB_USER=root \
		-e BACKUP_DEST_PATH=/tmp_backup_path \
		-e RESTIC_REPOSITORY=/backup \
		-e ENTRYPOINT_TARGET="$(ENTRYPOINT_TARGET)" \
		-v /tmp_backup_path \
		-v /media/backups-primary/restic-mysql:/backup \
		--network="env1_ycnet" \
		yukkuricraft/mysql-backup-restic

.PHONY: restore_mysql_from_backup
restore_mysql_from_backup:
	$(PRE) docker run \
		--env-file=secrets/minecraft_db.env \
		-e DB_SERVER=YC-$(ENV)-mysql \
		-e DB_USER=root \
		-e BACKUP_DEST_PATH=/tmp_backup_path \
		-e RESTIC_REPOSITORY=/backups \
		-e ENTRYPOINT_TARGET="/restic.sh restore 2>&1 /foo.out" \
		-v /tmp_backup_path \
		-v /media/backups-primary/restic:/backups \
		yukkuricraft/mysql-backup-restic

.PHONY: get_restic_snapshots_json
get_restic_snapshots_json:
	$(PRE) docker run \
		-e RESTIC_REPOSITORY=/backups \
		-e RESTIC_PASSWORD_FILE=/restic.password \
		-v /media/backups-primary/restic:/backups \
		-v $(PWD)/secrets/restic.password:/restic.password \
		restic/restic \
		--json \
		snapshots

.PHONY: get_restic_snapshots
get_restic_snapshots:
	$(PRE) docker run \
		-e RESTIC_REPOSITORY=/backups \
		-e RESTIC_PASSWORD_FILE=/restic.password \
		-v /media/backups-primary/restic:/backups \
		-v $(PWD)/secrets/restic.password:/restic.password \
		restic/restic \
		snapshots

# Prod Shortcuts

.PHONY: up_prod
up_prod: ENV=env1
up_prod: up

.PHONY: down_prod
down_prod: ENV=env1
down_prod: down

.PHONY: logs_prod
logs_prod: ENV=env1
logs_prod: logs

.PHONY: exec_prod
exec_prod: ENV=env1
exec_prod: exec

.PHONY: attach_prod
attach_prod: ENV=env1
attach_prod: attach