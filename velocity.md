# Velocity MC Proxy

Velocity config is located under `./secrets/velocity/velocity.toml`

Docker-compose files are generated using `./generate-docker-compose` or `make generate` or `make up`. We generate our compose config using the list of world groups defined in `world_group_config.yml`

We generate our compose file as there are a lot of repeated fields and values where the only difference is the world group name.

When adding a new worldgroup name to `world_group_config.yml`, there are a few pre-requisite steps to make it work.

1. Modify `./secrets/velocity/velocity.toml` to contain a server definition in the `[servers]` section with the appropriate container names. Ports should always be 25565.
2. Ensure the appropriate folders exist in both `/var/lib/yukkuricraft/<ENV>/<WORLDGROUP>/` as well as `./secrets/configs/<ENV>/<WORLDGROUP>/`
