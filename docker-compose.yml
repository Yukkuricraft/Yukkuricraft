version: "3.4"

x-extensions:
  mc_service_template: &mc_service_template
    depends_on:
      - velocity
      - mysql
    image: yukkuricraft/minecraft-server
    tty: true
    stdin_open: true
    restart: unless-stopped
    environment:
      YC_ENV: ${ENV_TYPE}
      MOTD: "${ENV_TYPE}-${MC_TYPE}_${MC_VERSION}[${PAPER_BUILD}]"
      EULA: 'true'
      COPY_PROD_WORLD: ${COPY_PROD_WORLD}
      VERSION: ${MC_VERSION}
      TYPE: ${MC_TYPE}
      PAPER_BUILD: ${PAPER_BUILD}
      STOP_SERVER_ANNOUNCE_DELAY: 5
      COPY_CONFIG_DEST: /data
      EXEC_DIRECTLY: 'true'
    networks:
      - ycnet

services:
  mysql:
    container_name: MySQL-${ENV}
    image: mysql/mysql-server:5.7
    volumes:
      - dbdata-${ENV}:/var/lib/mysql
    networks:
      - ycnet

  velocity:
    container_name: Velocity-${ENV}
    depends_on:
      - mysql
    image: itzg/bungeecord
    environment:
      TYPE: "VELOCITY"
      CFG_MOTD: "Powered by Docker"
    volumes:
      - velocity:/server
      - ./velocity/velocity.toml:/config/velocity.toml
      - ./secrets/forwarding.secret:/config/forwarding.secret
    ports:
      - 25600:25600
    networks:
      - ycnet

  mc_survival:
      <<: *mc_service_template
      container_name: YC-survival-${ENV}
      volumes:
        -
          type: bind
          source: ${MC_FS_ROOT}/prod/survival/worlds # This should always mount prod
          target: /worlds-bindmount-prod
          read_only: ${BINDMOUNT_RO}
        -
          type: bind
          source: ${MC_FS_ROOT}/prod/survival/plugins # This should always mount prod
          target: /plugins-bindmount-prod
          read_only: ${BINDMOUNT_RO}
        - mcdata_survival:/data
        - ./minecraft-data/${ENV}/survival/plugins:/yc-plugins
        - ./minecraft-data/${ENV}/survival/config:/yc-config

  mc_creative:
      <<: *mc_service_template
      container_name: YC-creative-${ENV}
      volumes:
        -
          type: bind
          source: ${MC_FS_ROOT}/prod/creative/worlds # This should always mount prod
          target: /worlds-bindmount-prod
          read_only: ${BINDMOUNT_RO}
        -
          type: bind
          source: ${MC_FS_ROOT}/prod/creative/plugins # This should always mount prod
          target: /plugins-bindmount-prod
          read_only: ${BINDMOUNT_RO}
        - mcdata_creative:/data
        - ./minecraft-data/${ENV}/creative/plugins:/yc-plugins
        - ./minecraft-data/${ENV}/creative/config:/yc-config


volumes:
  velocity:
  dbdata-prod:
  mcdata_survival:
  mcdata_creative:
  ycworldsvolume:
  ycpluginsvolume:

networks:
  ycnet:
