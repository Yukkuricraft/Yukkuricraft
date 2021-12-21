# Yukkuricraft

An attempt at uh... somewhat modernizing our setup after 9 years. Whee.

Jump to the Container Setup section for docker-compose notes

## Thoughts
- Containerizing our Minecraft install should allow for easier development, debugging, and general maintainability
    - Testing server upgrades would be much easier for example as you can just adjust some params and spin it up.
    - Containerization makes adding things like SSL easier.
    - We could expose different services and tools with their own reverse proxies... but this might be overkill due to lack of traffic volume
        - But could still use a single webserver to route traffic around the containers
    - Since I don't want to necessarily get into something as heavy as IAM with AWS/GCP, provisioning user access reliably on the YC host doesn't have an easy solution.
        - Containerization helps here as we can allow SSH access to individual containers or jump boxes for the non-sysadmins.
        - This still doesn't address CaC for the YC container host though.

## Architecture (WIP)

![Architecture Draft](https://lucid.app/publicSegments/view/c3058b49-3abb-4443-81e9-e89ee0b908e6/image.png)

### Major Outstanding Questions
- How do we "deploy" a new environment? Just make a copy of a docker-compose and `up` it? That sounds lazy/brittle
    - Do we utilize git branches for separating environments? Setting up an entire deployment pipeline sounds very overkill.
    - Any way to utilize Github Actions? Likely difficult due to needing to talk back to our onprem host meaning need to set up some API which is more work.
- Nginx Gateway
    - Single gateway to serve all containers? This would be pretty difficult in conjunction with using branches.
    - Serve on different subdomains based on branch and its configurations??
        - Could deploy based on branches then, but which branches to "enable"? Or do we just deploy for every branch? This seems unscalable/prone to human error
- Minecraft Root Directory Layout
    - By default, volumes mapped to local FS will go under `/var/lib/yukkuricraft/`
        - Production - ie the instance you connect to at `mc.yukkuricraft.net`, will go under `yukkuricraft/prod/`
        - Symlink `~/yukkuricraft` to `/var/lib/yukkuricraft/`
    - Plugins
        - `/var/lib/yukkuricraft/prod/plugins:/app/plugins`
    - Worlds
        - `/var/lib/yukkuricraft/prod/worlds:/app/worlds`
    - Jars?
        - Hm... Maybe keep a list of all jars we use in an S3 and use from there?
        - Just keep locally?
        - ... Just be lazy and commit to VCS? (Ick)

### Hahaha
- https://github.com/itzg/docker-minecraft-server
- This makes life easier.

## Required "Functionality"
- Ability to easily spin up new minecraft instances
- Ability to easily connect to and use the console on a given instance
- Backup-friendly filesystem layout with container volumes

## Container Setup
- We're using the `itzg/minecraft-server` image See [Documentatino](https://github.com/itzg/docker-minecraft-server/blob/master/README.md)
- Worlds are setup in a `worlds/` subdirectory as per `bukkit.yml` config.
- Configs are copied from `minecraft-data/configs/` into the container working dir
    - Likewise with plugins

## Notes
- OpenJDK 11
- Ahaha, `itzg/*` images to the rescue
