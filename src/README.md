# Yukkuricraft Backend & Management Code

WIP

# Api Module
Backend server written in python + flask. Allows for remote management of the server as well as viewing info and status.

- We use Flask for API
- We use Flask-SocketIO for websockets/socketio

See the Module's [README.md](api/) for API level details

## Server API

- Containers, interacting with servers

## Backups API

- Listing, creating, deleting, and restoring backups using Restic.
  - Currently only supports Minecraft containers

## Environment API

- Managing, creating, deleting, editing environments (which contain containers)

## Files API

- API for read/writing files on the server and within containers.
  - Should eventually get deprecated, but used to modify cluster configs for now.

## Socket IO API

- API for two-way communication between frontend/backend.
  - Is not currently used.

# Generator Module
Source for dynamically generating config files used at runtime via user-defined config. Users use [YakumoDash](https://github.com/Yukkuricraft/YakumoDash) to interact with the config. 

Configs are generated at various points such as when a user edits the config or when servers are restarted.

# Common Module

Contains commonly used code between the API and Generator modules.