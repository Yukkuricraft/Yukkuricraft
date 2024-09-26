#!/bin/env python3

import os
import socket

from pprint import pformat
from typing import Dict
from pathlib import Path

from src.api.constants import API_HOST

from src.common.config import load_env_config
from src.common.paths import ServerPaths
from src.common.environment import Env
from src.common.logger_setup import logger
from src.common.helpers import log_exception

from src.generator.base_generator import BaseGenerator

"""
Generate .env files for use with docker-compose.

Since .env files only accept key-value pairs, our implementation makes a Dict[str, str] assumption for the generated config.
As such an ENV.toml that defines non-string values for keys in '[cluster-variables]' may cause issues.
"""


class EnvFileGen(BaseGenerator):
    generated_env_file_name: str
    generated_env_file_path: Path

    generated_env_config: Dict[str, str]

    def __init__(self, env: Env):
        super().__init__(env)

        self.generated_env_file_path = ServerPaths.get_generated_env_file_path(env.name)
        if not self.generated_env_file_path.parent.exists():
            self.generated_env_file_path.parent.mkdir()

    def run(self):
        self.generate_env_file()
        self.dump_generated_env_file()

    def generate_env_file(self):
        self.generated_env_config = self.env.cluster_vars.as_dict()

        self.generated_env_config["ENV"] = self.env.name
        self.generated_env_config["API_HOST"] = API_HOST
        self.generated_env_config["UID"] = os.getuid()
        self.generated_env_config["GID"] = os.getgid()

        # yc-api relies on hostname to determine prod vs non-prod envs. Docker containers
        # will always return the container id for hostname so we configure the hostname in the compose file.
        self.generated_env_config["HOST_HOSTNAME"] = socket.gethostname()

        self.generate_mysql_env_vars()
        self.generate_postgres_env_vars()

    def generate_mysql_env_vars(self):
        mysql_user = ""
        mysql_pw = ""
        mysql_db = ""

        try:
            db_env_config = load_env_config(
                ServerPaths.get_minecraft_db_env_file_path()
            )
            mysql_user = db_env_config["MYSQL_USER"]
            mysql_pw = db_env_config["MYSQL_PASSWORD"]
            mysql_db = db_env_config["MYSQL_DATABASE"]
        except:
            raise RuntimeError(
                "Was unable to get MySQL user/pass from the db env file!"
            )

        self.generated_env_config["YC_MYSQL_DB"] = mysql_db
        self.generated_env_config["YC_MYSQL_HOST"] = f"YC-{self.env.name}-mysql"
        self.generated_env_config["YC_MYSQL_USER"] = mysql_user
        self.generated_env_config["YC_MYSQL_PASS"] = mysql_pw

    def generate_postgres_env_vars(self):
        pg_user = "mine"
        pg_pw = ""

        try:
            with open(ServerPaths.get_pg_pw_file_path(), "r") as f:
                pg_pw = f.read().strip()
        except:
            raise RuntimeError(
                "Was unable to get Postgres pass from the postgres_pw file!"
            )

        self.generated_env_config["YC_POSTGRES_HOST"] = f"YC-{self.env.name}-postgres"
        self.generated_env_config["YC_POSTGRES_USER"] = pg_user
        self.generated_env_config["YC_POSTGRES_PASS"] = pg_pw

    @staticmethod
    def dump_write_cb(f, config):
        logger.debug(pformat(config))
        for key, value in config.items():
            f.write(f'{key}="{value}"\n'.encode("utf8"))

    def dump_generated_env_file(self):
        logger.info(f"Generating new {self.generated_env_file_path}...")

        self.write_config(
            self.generated_env_file_path,
            self.generated_env_config,
            (
                "#\n"
                "# THIS FILE WAS AUTOMATICALLY GENERATED\n"
                "# DO NOT MODIFY MANUALLY\n"
                "# CHANGES WILL BE OVERWRITTEN ON RESTART\n"
                "#"
                f"# MODIFY `env/{self.env.name}.toml` FOR PERMANENT CHANGES"
                "#\n\n"
            ),
            EnvFileGen.dump_write_cb,
        )

        logger.info("Done.")
