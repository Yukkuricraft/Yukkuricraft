import stat
from pathlib import Path
from typing import Any

BASE_DATA_PATH = Path("/var/lib/yukkuricraft")
REPO_ROOT_PATH = Path(__file__).parent.parent.parent  # G w o s s

VELOCITY_FORWARDING_SECRET_PATH: Path = (
    REPO_ROOT_PATH / "secrets" / "velocity" / "forwarding.secret"
)

PAPER_GLOBAL_TEMPLATE_PATH: Path = Path("templates/paper-global.tpl.yml")
DOCKER_COMPOSE_TEMPLATE_PATH: Path = Path("templates/docker-compose.tpl.yml")
VELOCITY_CONFIG_TEMPLATE_PATH: Path = Path("templates/velocity.tpl.toml")
SERVER_PROPERTIES_TEMPLATE_PATH: Path = Path("templates/server.tpl.properties")


DEFAULT_CHMOD_MODE = (
    stat.S_IRUSR
    | stat.S_IWUSR
    | stat.S_IXUSR
    | stat.S_IRGRP
    | stat.S_IWGRP
    | stat.S_IXGRP
    | stat.S_IROTH
    | stat.S_IXOTH
)
