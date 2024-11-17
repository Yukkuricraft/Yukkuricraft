import json
from pathlib import Path
from typing import Any, Dict, List
import pytest  # type: ignore

from pydantic import ValidationError  # type: ignore
from src.api.lib import (
    BackupAlreadyInProgressError,
    CannotRestoreWhileContainerUpError,
    RestoreAlreadyInProgressError,
)
from src.api.lib.backup_management import BackupManagement
from src.common.environment import Env  # type: ignore


@pytest.fixture
def backup_mgmt(mocker) -> BackupManagement:
    mock_docker_mgmt = mocker.MagicMock()
    mock_docker_mgmt.client.containers.run.return_value = "[]"

    return BackupManagement(docker_management=mock_docker_mgmt)


@pytest.fixture
def restic_backup_obj() -> Dict[str, Any]:
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
def restic_tags_list() -> List[str]:
    return ["tag1", "tag2"]


@pytest.fixture
def env1_object(mocker):
    env_mock = mocker.MagicMock()
    env_mock.name = "env1"
    return env_mock


@pytest.fixture
def world_group() -> str:
    return "lobby"


@pytest.fixture
def restic_target_id() -> str:
    return "target-id-foo"


class TestBackupManagement:
    """Backup Management lib unit tests"""

    def test__list_backups_by_env_and_tags__pydantic_validation_error(
        self,
        backup_mgmt: BackupManagement,
        env1_object: Env,
        restic_backup_obj,
        restic_tags_list: List[str],
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

    def test__list_backups_by_env_and_tags__success(
        self,
        backup_mgmt: BackupManagement,
        env1_object: Env,
        restic_backup_obj,
        restic_tags_list,
    ):
        """Validates a 'happy case' of the Restic container returning a single valid backup as json and we return it as a list of Backup objects"""

        backup_mgmt.docker_client.containers.run.return_value = (
            f"[{json.dumps(restic_backup_obj)}]"
        )
        backup_mgmt.list_backups_by_env_and_tags(env=env1_object, tags=restic_tags_list)

    def test__backup_minecraft__backup_already_in_progress_error(
        self, backup_mgmt: BackupManagement, env1_object: Env, world_group: str
    ):
        """Test that we get an error if a backup is already in progress for this environment and world group."""

        backup_mgmt.docker_management.is_container_up.return_value = True

        with pytest.raises(BackupAlreadyInProgressError):
            backup_mgmt.backup_minecraft(env1_object, world_group)

    def test__backup_minecraft__backup_entrypoint_command_if_container_up(
        self, backup_mgmt: BackupManagement, env1_object: Env, world_group: str
    ):
        """Test the entrypoint_command we use for the backup container is the minecraft container is up."""

        mc_server_up = True
        backup_mgmt.docker_management.is_container_up.side_effect = [
            False,
            mc_server_up,
        ]
        backup_mgmt.docker_client.containers.run.return_value = f"[]".encode("utf8")

        backup_mgmt.backup_minecraft(env1_object, world_group)
        env_vars = backup_mgmt.docker_client.containers.run.call_args.kwargs[
            "environment"
        ]

        assert (
            "/usr/bin/backup" in env_vars["ENTRYPOINT_TARGET"]
        ), "Expected ENTRYPOINT_TARGET to call '/usr/bin/backup' if mc container is up!"

    def test__backup_minecraft__backup_entrypoint_command_if_container_down(
        self, backup_mgmt: BackupManagement, env1_object: Env, world_group: str
    ):
        """Test the entrypoint_command we use for the backup container is the minecraft container is down."""
        mc_server_up = False
        backup_mgmt.docker_management.is_container_up.side_effect = [
            False,
            mc_server_up,
        ]
        backup_mgmt.docker_client.containers.run.return_value = f"[]".encode("utf8")

        backup_mgmt.backup_minecraft(env1_object, world_group)
        env_vars = backup_mgmt.docker_client.containers.run.call_args.kwargs[
            "environment"
        ]

        assert (
            "bash /restic.sh" in env_vars["ENTRYPOINT_TARGET"]
        ), "Expected ENTRYPOINT_TARGET to call 'bash /restic.sh' if mc container is up!"

    def test__archive_directory__creates_archive_directory(
        self, tmp_path: Path, backup_mgmt: BackupManagement
    ):
        """Test that the archive_directory() method creates a new archive directory if it doesn't already exist."""

        suffix = "_testsuffix"
        backup_mgmt.archive_directory(
            tmp_path,
            suffix,
        )

        expected_archive_path = f"{tmp_path}{suffix}"
        assert Path(
            expected_archive_path
        ).exists, (
            f"Expected archive directory '{expected_archive_path} to get created!'"
        )

    def test__archive_directory__extra_directories_removed(
        self, tmp_path: Path, backup_mgmt: BackupManagement
    ):
        """Test that the final number of directories matches the max_archives count

        Ie, tests the "old archive deletion" logic runs correctly.
        """

        suffix = "_testsuffix"
        expected_archive_path = Path(f"{tmp_path}{suffix}")
        max_archives = 10

        for idx in range(max_archives + 1):
            (expected_archive_path / f"{tmp_path.name}_{idx}").mkdir(
                parents=True, exist_ok=True
            )

        backup_mgmt.archive_directory(
            tmp_path,
            suffix,
            max_archives,
        )

        num_archives = len(list(expected_archive_path.iterdir()))
        assert (
            num_archives == max_archives
        ), f"Expected there to be a max of '{max_archives}' archive directories but found '{num_archives}'!"

    def test__archive_directory__existing_directories_under_max_count_remain(
        self, tmp_path: Path, backup_mgmt: BackupManagement
    ):
        """Test that the final number of directories matches the max_archives count

        Ie, tests the "old archive deletion" logic runs correctly.
        """

        suffix = "_testsuffix"
        expected_archive_path = Path(f"{tmp_path}{suffix}")
        max_archives = 10
        archives_to_premake = max_archives - 2

        should_exist_archives = []
        for idx in range(archives_to_premake):
            archive_dir = expected_archive_path / f"{tmp_path.name}_{idx}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            should_exist_archives.append(archive_dir)

        backup_mgmt.archive_directory(
            tmp_path,
            suffix,
            max_archives,
        )

        num_archives = len(list(expected_archive_path.iterdir()))
        assert (
            num_archives == archives_to_premake + 1
        ), f"Expected there to be a max of '{archives_to_premake + 1}' archive directories but found '{num_archives}'!"

        for archive in should_exist_archives:
            assert (
                archive.exists()
            ), f"Expected a premade archive directory '{expected_archive_path}' to exist but it didn't!"

    def test__archive_directory__success(
        self, mocker, tmp_path: Path, backup_mgmt: BackupManagement
    ):
        """Tests that the target dir to archive gets archived as expected"""

        suffix = "_testsuffix"
        expected_archive_path = Path(f"{tmp_path}{suffix}")
        max_archives = 10

        file_in_archive = tmp_path / "foofile"
        file_in_archive.touch()

        time_time = 123456789
        mocker.patch("time.time", return_value=time_time)
        backup_mgmt.archive_directory(
            tmp_path,
            suffix,
            max_archives,
        )

        archived_file = (
            expected_archive_path
            / f"{tmp_path.name}-{time_time}"
            / file_in_archive.name
        )

        assert (
            archived_file.exists()
        ), f"Expected a premade archive directory '{expected_archive_path}' to exist but it didn't!"

    def test__restore_minecraft__cannot_restore_while_container_up_error(
        self,
        backup_mgmt: BackupManagement,
        env1_object: Env,
        world_group: str,
        restic_target_id: str,
    ):
        """Ensure we get an error if the container we're trying to restore to is currently running."""

        backup_mgmt.docker_management.is_container_up.side_effect = [True]

        with pytest.raises(CannotRestoreWhileContainerUpError):
            backup_mgmt.restore_minecraft(env1_object, world_group, restic_target_id)

    def test__restore_minecraft__restore_already_in_progress_error(
        self,
        backup_mgmt: BackupManagement,
        env1_object: Env,
        world_group: str,
        restic_target_id: str,
    ):
        """Ensure we get an error if there is a restore already in progress for this world group and env."""

        backup_mgmt.docker_management.is_container_up.side_effect = [False, True]

        with pytest.raises(RestoreAlreadyInProgressError):
            backup_mgmt.restore_minecraft(env1_object, world_group, restic_target_id)

    def test__restore_minecraft__success(
        self,
        mocker,
        backup_mgmt: BackupManagement,
        env1_object: Env,
        world_group: str,
        restic_target_id: str,
    ):
        """Ensures given no container state issues, the docker call to run the restore sidecar container is executed"""

        backup_mgmt.docker_management.is_container_up.side_effect = [False, False]
        backup_mgmt.docker_client.containers.run.return_value = ""
        mocker.patch(
            "src.api.lib.backup_management.BackupManagement.archive_directory",
            return_value=None,
        )

        backup_mgmt.restore_minecraft(env1_object, world_group, restic_target_id)

        backup_mgmt.docker_client.containers.run.assert_called_once()
