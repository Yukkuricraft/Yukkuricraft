import json
from unittest.mock import PropertyMock
import pytest  # type: ignore

from pydantic import ValidationError  # type: ignore
from src.api.lib import BackupAlreadyInProgressError
from src.api.lib.backup_management import BackupManagement  # type: ignore


@pytest.fixture
def backup_mgmt(mocker):
    mock_docker_mgmt = mocker.MagicMock()
    mock_docker_mgmt.client.containers.run.return_value = "[]"

    return BackupManagement(docker_management=mock_docker_mgmt)


@pytest.fixture
def restic_backup_obj():
    """Only contains required (non Optional) fields"""
    return {
        "excludes": ["string"],
        "gid": 9999,
        "hostname": "a-hostname",
        "id": "a-regular-id",
        "paths": ["path1", "path2"],
        "program_version": "ver0.1",
        "short_id": "a-short-id",
        "tags": ["tag1", "tag2"],
        "time": "1970-01-01T00:00:00",
        "tree": "a-tree-string",
        "uid": 9998,
        "username": "a-username",
    }


@pytest.fixture
def restic_tags_list():
    return ["tag1", "tag2"]


@pytest.fixture
def env1_object(mocker):
    env_mock = mocker.MagicMock()
    env_mock.name = "env1"
    return env_mock

@pytest.fixture
def world_group():
    return "lobby"


class TestBackupManagement:
    """Backup Management lib unit tests"""

    def test_list_backups_by_env_and_tags_pydantic_validation_error(
        self, backup_mgmt, env1_object, restic_backup_obj, restic_tags_list
    ):
        """Validates that we get a pydantic Validation Error if restic returns a Backup object without all the expected fields."""
        for field in restic_backup_obj.keys():
            restic_backup_obj_minus_one_field = {
                k: v for k, v in restic_backup_obj.items() if k != field
            }
            backup_mgmt.docker_client.containers.run.return_value = (
                f"[{json.dumps(restic_backup_obj_minus_one_field)}]"
            )

            with pytest.raises(ValidationError):
                backup_mgmt.list_backups_by_env_and_tags(
                    env=env1_object, tags=restic_tags_list
                )

    def test_list_backups_by_env_and_tags_success(
        self, backup_mgmt, env1_object, restic_backup_obj, restic_tags_list
    ):
        """Validates a 'happy case' of the Restic container returning a single valid backup as json and we return it as a list of Backup objects"""
        backup_mgmt.docker_client.containers.run.return_value = (
            f"[{json.dumps(restic_backup_obj)}]"
        )
        backup_mgmt.list_backups_by_env_and_tags(env=env1_object, tags=restic_tags_list)

    def test_backup_minecraft_backup_already_in_progress_error(self, backup_mgmt, env1_object, world_group):
        backup_mgmt.docker_management.is_container_up.return_value = True

        with pytest.raises(BackupAlreadyInProgressError):
            backup_mgmt.backup_minecraft(env1_object, world_group)

    def test_backup_minecraft_backup_entrypoint_command_if_container_up(self, backup_mgmt, env1_object, world_group):
        mc_server_up = True
        backup_mgmt.docker_management.is_container_up.side_effect = [False, mc_server_up]
        backup_mgmt.docker_client.containers.run.return_value = (
            f"[]".encode("utf8")
        )

        backup_mgmt.backup_minecraft(env1_object, world_group)
        env_vars = backup_mgmt.docker_client.containers.run.call_args.kwargs["environment"]
        
        assert "/usr/bin/backup" in env_vars["ENTRYPOINT_TARGET"], "Expected ENTRYPOINT_TARGET to call '/usr/bin/backup' if mc container is up!"

    def test_backup_minecraft_backup_entrypoint_command_if_container_down(self, backup_mgmt, env1_object, world_group):
        mc_server_up = False
        backup_mgmt.docker_management.is_container_up.side_effect = [False, mc_server_up]
        backup_mgmt.docker_client.containers.run.return_value = (
            f"[]".encode("utf8")
        )

        backup_mgmt.backup_minecraft(env1_object, world_group)
        env_vars = backup_mgmt.docker_client.containers.run.call_args.kwargs["environment"]
        
        assert "bash /restic.sh" in env_vars["ENTRYPOINT_TARGET"], "Expected ENTRYPOINT_TARGET to call 'bash /restic.sh' if mc container is up!"

    def test_archive_directory(self, backup_mgmt):
        to_archive = "asd"
        suffix = "asdf"
        # backup_mgmt.archive_directory(
        #     to_archive,
        #     suffix,
        # )
        pass

    def test_restore_minecraft(self, mocker):
        pass
