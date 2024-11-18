# API Module
## Code At A High Level
- Globals/constants are defined based on provided `CONFIGURATION_TYPE` env var in [`src/constants.py`](constants.py).
- [`src/blueprints/`](blueprints/) contain the api setup.
- [`src/lib/`](lib/) contains the logic.
  - Most interesting files are:
    - [`src/auth.py`](lib/auth.py)
    - [`src/lib/backup_management.py`](lib/backup_management.py)
    - [`src/lib/docker_management.py`](lib/docker_management.py)

## API Docs
- [Check OpenAPI Docs](https://api.yukkuricraft.net/openapi/)