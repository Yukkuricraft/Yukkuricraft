## Endpoints?
(May be outdated)

All authenticated endpoints also take an `OPTIONS` method request for CORS handling.

### Auth
Endpoints related to authenticating.

|Method|Endpoint|Purpose|
|------|--------|-------|
|`POST`|`/auth/login`|Logging into app|
|`GET`|`/auth/me`|Endpoint hit to validate user still logged into app. All authenticated pages must succeed this request.|
|`GET`|`/auth/createdbdeleteme`|Disabled endpoint that's enabled any time we need initial DB setup. Is a hack. Needs to be replaced.|


### Files
Endpoints for managing server files on the host FS.

|Method|Endpoint|Purpose|
|------|--------|-------|
|`POST`|`/files/list`|An `ls` on the directory specified in the `POST`` body. Should really be a `GET`|
|`POST`|`/files/read`|Read contents of a file. Should really be a `GET`|
|`POST`|`/files/write`|Writes contents to a file.|


### Environment 
Endpoints related to management of environments

|Method|Endpoint|Purpose|
|------|--------|-------|
|`POST`|`/environment/create_env`|Create new env|
|`DELETE`|`/environment/<env_str>`|To delete env `env_str`|
|`POST`|`/environment/<env_str>/generate-configs`|Regenerates all configs for the env specified|
|`GET`|`environment/list-envs-with-configs`|List all defined envs with valid configs|


### Server
Endpoints related to management of containers

Should probably be called containers and not "server".

|Method|Endpoint|Purpose|
|------|--------|-------|
|`GET`|`/server/<env_str>/containers`|List all defined containers for an `env_str`|
|`GET`|`/server/<env_str>/containers/active`|List subset of defined containers that are currently up and running in Docker.|
|`POST`|`/server/<env_str>/containers/up`|Starts up all containers for `env_str`|
|`POST`|`/server/<env_str>/containers/up_one`|Start one container in `env_str`|
|`POST`|`/server/<env_str>/containers/down`|Shuts down all containers for `env_str`|
|`POST`|`/server/<env_str>/containers/down_one`|Kills one container in `env_str`|
|`POST`|`/server/containers/copy-configs-to-bindmount`|Copy configs from the container FS to host FS by copying files back to the bindmounts.|


### Sockets
Endpoints related socketio.

SocketIO lol.