# Yukkuricraft

An attempt at uh... somewhat modernizing our setup after 9 years. Whee.

## Thoughts
- Containerizing our Minecraft install should allow for easier development, debugging, and general maintainability
    - Testing server upgrades would be much easier for example as you can just adjust some params and spin it up.
    - Containerization makes adding things like SSL easier.
    - We could expose different services and tools with their own reverse proxies... but this might be overkill due to lack of traffic volume
        - But could still use a single webserver to route traffic around the containers
    - Since I don't want to necessarily get into something as heavy as IAM with AWS/GCP, provisioning user access reliably on the YC host doesn't have an easy solution.
        - Containerization helps here as we can allow SSH access to individual containers or jump boxes for the non-sysadmins.
        - This still doesn't address CaC for the YC container host though.

## Architecture

![Architecture Draft](https://lucid.app/publicSegments/view/c3058b49-3abb-4443-81e9-e89ee0b908e6/image.png)

### Major Outstanding Questions
- How do we "deploy" a new environment? Just make a copy of a docker-compose and `up` it? That sounds lazy/brittle
    - Do we utilize git branches for separating environments? Setting up an entire deployment pipeline sounds very overkill.
    - Any way to utilize Github Actions? Likely difficult due to needing to talk back to our onprem host meaning need to set up some API which is more work.
- Nginx Gateway
    - Single gateway to serve all containers? This would be pretty difficult in conjunction with using branches.
    - Serve on different subdomains based on branch and its configurations??
        - Could deploy based on branches then, but which branches to "enable"? Or do we just deploy for every branch? This seems unscalable/prone to human error
