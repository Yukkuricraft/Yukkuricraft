# Yukkuricraft
Containerized Yukkuricraft

## Architecture (WIP)
![Architecture Draft](https://lucid.app/publicSegments/view/c3058b49-3abb-4443-81e9-e89ee0b908e6/image.png)

## Description

This is our attempt at containerizing the Yukkuricraft minecraft server utilizing `itzg/minecraft-server`.

We support two "types" of environments - `prod` and `dev`.
- The `prod` type env is a singular environment - ie only one prod.
- There can however be multiple `dev` type envs. We standardize our names as `dev#` where # is an int starting at 1.
- Thus, as a minimal setup we have a `prod` and `dev1` environments.

We use a singular `docker-compose.yml` file which uses a combination of buildtime and runtime environment variable substitutions. We recommend that you do _not_ run `docker-compose` or `docker` commands manually, but rather to use the `Makefile` targets provided. See [Running Containers](#running-containers).

We also utilize a custom `scripts/start.sh` script to do some filesystem setup for us prior to starting the server. As such, we also create a short `yukkuricraft/minecraft-server` image as defined in `images/minecraft-server/Dockerfile`.

## Environments

The `prod` and `dev` environment **types** have a special relationship with each other.

Our production world data currently resides on the container host's filesystem as configured in the `env/prod.env` file. More specifically, our `docker-compose.yml` bind mounts this world data to the `/worlds-bindmount` directory inside the container. This is regardless of environment type.

Additionally, we configure the minecraft server to treat `/yc-worlds` as the container path for all world data.

From here, behavior diverges based on environment type:

#### Prod
We simply symlink the contents of `/worlds-bindmount` to `/yc-worlds`. This effectively bindmounts the container host's production world data to the world data path within the container. Thus in theory, anytime the world data is saved on the production server, the world state should be written back to the host FS.

We recommend to run the `make save_world` command for convenience when needing to immediately write world state to disk.

#### Dev
For development environments, we introduce two new "features".
- First, the world data used for dev environments are stored on a docker volume rather than binding to host FS.
- Second, we introduce the ability to toggle "Copy production world data" on startup with the correct flags set.

To accomplish this, we setup our volumes and mounts slightly differently from production:
- First, we bind mount the production world data to `/worlds-bindmount` same as production.
- Next, we create a docker volume mounted to `/worlds-volume`. This volume will contain all our world data.
- Finally, we create a symlink so `/yc-worlds` points to `/worlds-volume`.

This roundabout setup is necessary as we want to effectively use `/yc-worlds` as both a bind mount for production and a docker volume for development. Since we cannot configure docker-compose to use both, we instead use the `scripts/start.sh` script to setup our symlinks based on environment type.

<h2 id="running-containers">Running Containers</h2>

- All containers are named with the environment added as a suffix. Eg, `YC-prod`, `MySQL-prod`, `YC-dev`, etc
- All container management should generally be done using `Makefile` targets. **All commands by default will target the `dev1` environment.**
    - You may prepend an ENV var declaration to any `make` target to change the environment. Eg, `make ENV=prod up` or `make ENV=prod save_world`

Below are the commonly used commands:
|Command|Description|
|-------|-----------|
|`make up`|Starts the server on the specified environment.|
|`make down`|Kills containers in the specified environment.|
|`make logs`|Runs `docker-compose logs` for the specified environment's containers.|
|`make attach`|Runs `docker attach` to the `YC-${ENV}` container. **This is attaching to Console.** Be aware that ctrl+c kills the server. Detaching is done with `Ctrl+P`, then `Ctrl+Q`.|
|`make purge`|Purges all docker volumes that are not in use. Must down containers first.|
|`make save_world`|Runs `save-all` inside the console of the `YC-${ENV}` container. **Writes the world to disk.**|

See the contents of `Makefile` for a full list of valid targets.

## Outstanding Questions
- Logs?
- Plugins and configs?

## See Also
- [Initial Thoughts - First Draft README](docs/initial_thoughts.md)
