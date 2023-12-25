import stat
from typing import  Any

DOCKER_COMPOSE_TEMPLATE_NAME: str = "templates/docker-compose.tpl.yml"
VELOCITY_CONFIG_TEMPLATE_NAME: str = "templates/velocity.tpl.toml"

DEFAULT_CHMOD_MODE = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR \
                      | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP \
                      | stat.S_IROTH                | stat.S_IXOTH