import json
from pathlib import Path
from typing import Any, Dict, List
import pytest  # type: ignore

from pydantic import ValidationError
from pytest_mock import MockerFixture  # type: ignore
from src.api.lib import (
    Backup,
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
        "gid": 9999,
        "hostname": "a-hostname",
        "id": "a-regular-id",
        "paths": ["path1", "path2"],
        "program_version": "ver0.1",
        "short_id": "a-short-id",
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


@pytest.fixture
def target_worlds() -> List[str]:
    return [
        "world1",
        "world2",
    ]


@pytest.fixture
def restic_command() -> str:
    return "some restic command here"


@pytest.fixture
def bypass_running_container_restriction() -> bool:
    return False


@pytest.fixture
def world_file() -> str:
    return "world.file"


@pytest.fixture
def archive_directories_fs_setup(
    tmp_path: Path, target_worlds: List[str], world_file: str
) -> Path:
    for target_world in target_worlds:
        target_world_path = tmp_path / target_world
        target_world_path.mkdir(exist_ok=True, parents=True)
        file_in_world = target_world_path / world_file
        file_in_world.touch()

    return tmp_path


class TestBackupManagement:
    """Backup Management lib unit tests"""

    def test__call_restic__success(
        self,
        mocker: MockerFixture,
        backup_mgmt: BackupManagement,
        restic_command: str,
    ):
        # SETUP
        backup_mgmt.docker_management.is_container_up.side_effect = [False, False]
        backup_mgmt.docker_client.containers.run.return_value = ""
        mocker.patch(
            "src.api.lib.backup_management.BackupManagement.archive_directory",
            return_value=None,
        )

        expected_field1 = "field1"
        expected_val1 = {"foo": "bar"}
        expected_field2 = "field2"
        expected_val2 = "val2"

        override_args = {
            expected_field1: expected_val1,
            "environment": {
                expected_field2: expected_val2,
            },
        }

        # EXECUTE
        backup_mgmt.call_restic(
            restic_command,
            override_args,
        )

        # ASSERT
        call_kwargs = backup_mgmt.docker_client.containers.run.call_args.kwargs

        assert (
            call_kwargs["command"] == restic_command
        ), "Expected to have passed supplied command to .run()!"

        assert (
            call_kwargs[expected_field1] == expected_val1
        ), "Expected new override arg to be supplied to .run()!"

        assert (
            call_kwargs["environment"][expected_field2] == expected_val2
        ), "Expected override arg to be merged with default arg vals when passed to .run()!"

    def test__list_backups_by_env_and_tags__pydantic_validation_error(
        self,
        backup_mgmt: BackupManagement,
        env1_object: Env,
        restic_backup_obj,
        restic_tags_list: List[str],
    ):
        """Validates that we get a pydantic Validation Error if restic returns a Backup object without all the expected fields."""

        for field in restic_backup_obj.keys():
            # SETUP
            restic_backup_obj_minus_one_field = {
                k: v for k, v in restic_backup_obj.items() if k != field
            }
            backup_mgmt.docker_client.containers.run.return_value = (
                f"[{json.dumps(restic_backup_obj_minus_one_field)}]"
            )

            with pytest.raises(ValidationError):
                # EXECUTE
                # ASSERT
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

        # SETUP
        backup_mgmt.docker_client.containers.run.return_value = (
            f"[{json.dumps(restic_backup_obj)}]"
        )

        # EXECUTE
        result = backup_mgmt.list_backups_by_env_and_tags(
            env=env1_object, tags=restic_tags_list
        )

        # ASSERT
        assert result == [
            Backup(**restic_backup_obj)
        ], f"Did not get expected restic backup object back from list_backups_by_env_and_tags()!"

    def test__backup_minecraft__backup_already_in_progress_error(
        self, backup_mgmt: BackupManagement, env1_object: Env, world_group: str
    ):
        """Test that we get an error if a backup is already in progress for this environment and world group."""

        # SETUP
        backup_mgmt.docker_management.is_container_up.return_value = True

        with pytest.raises(BackupAlreadyInProgressError):
            # EXECUTE
            # ASSERT
            backup_mgmt.backup_minecraft(env1_object, world_group)

    def test__backup_minecraft__backup_entrypoint_command_if_container_up(
        self, backup_mgmt: BackupManagement, env1_object: Env, world_group: str
    ):
        """Test the entrypoint_command we use for the backup container is the minecraft container is up."""

        # SETUP
        mc_server_up = True
        backup_mgmt.docker_management.is_container_up.side_effect = [
            False,
            mc_server_up,
        ]
        backup_mgmt.docker_client.containers.run.return_value = f"[]".encode("utf8")

        # EXECUTE
        backup_mgmt.backup_minecraft(env1_object, world_group)

        # ASSERT
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
        # SETUP
        mc_server_up = False
        backup_mgmt.docker_management.is_container_up.side_effect = [
            False,
            mc_server_up,
        ]
        backup_mgmt.docker_client.containers.run.return_value = f"[]".encode("utf8")

        # EXECUTE
        backup_mgmt.backup_minecraft(env1_object, world_group)

        # ASSERT
        env_vars = backup_mgmt.docker_client.containers.run.call_args.kwargs[
            "environment"
        ]
        assert (
            "bash /restic.sh" in env_vars["ENTRYPOINT_TARGET"]
        ), "Expected ENTRYPOINT_TARGET to call 'bash /restic.sh' if mc container is up!"

    def test__archive_directory__creates_archive_directory(
        self,
        target_worlds: List[str],
        archive_directories_fs_setup: Path,
        backup_mgmt: BackupManagement,
    ):
        """Test that the archive_directory() method creates a new archive directory if it doesn't already exist."""

        # SETUP
        suffix = "_testsuffix"

        # EXECUTE
        backup_mgmt.archive_directory(
            target_worlds,
            archive_directories_fs_setup,
            suffix,
        )

        # ASSERT
        expected_archive_path = f"{archive_directories_fs_setup}{suffix}"
        assert Path(
            expected_archive_path
        ).exists, (
            f"Expected archive directory '{expected_archive_path} to get created!'"
        )

    def test__archive_directory__extra_directories_removed(
        self,
        target_worlds: List[str],
        archive_directories_fs_setup: Path,
        backup_mgmt: BackupManagement,
    ):
        """Test that the final number of directories matches the max_archives count

        Ie, tests the "old archive deletion" logic runs correctly.
        """

        # SETUP
        suffix = "_testsuffix"
        expected_archive_path = Path(f"{archive_directories_fs_setup}{suffix}")
        max_archives = 10

        for idx in range(max_archives + 1):
            (
                expected_archive_path / f"{archive_directories_fs_setup.name}_{idx}"
            ).mkdir(parents=True, exist_ok=True)

        # EXECUTE
        backup_mgmt.archive_directory(
            target_worlds,
            archive_directories_fs_setup,
            suffix,
            max_archives,
        )

        # ASSERT
        num_archives = len(list(expected_archive_path.iterdir()))
        assert (
            num_archives == max_archives
        ), f"Expected there to be a max of '{max_archives}' archive directories but found '{num_archives}'!"

    def test__archive_directory__existing_directories_under_max_count_remain(
        self,
        target_worlds: List[str],
        archive_directories_fs_setup: Path,
        backup_mgmt: BackupManagement,
    ):
        """Test that the final number of directories matches the max_archives count

        Ie, tests the "old archive deletion" logic runs correctly.
        """

        # SETUP
        suffix = "_testsuffix"
        expected_archive_path = Path(f"{archive_directories_fs_setup}{suffix}")
        max_archives = 10
        archives_to_premake = max_archives - 2

        world_file = "world.file"
        for target_world in target_worlds:
            target_world_path = archive_directories_fs_setup / target_world
            target_world_path.mkdir(exist_ok=True, parents=True)
            file_in_world = target_world_path / world_file
            file_in_world.touch()

        should_exist_archives = []
        for idx in range(archives_to_premake):
            archive_dir = (
                expected_archive_path / f"{archive_directories_fs_setup.name}_{idx}"
            )
            archive_dir.mkdir(parents=True, exist_ok=True)

            should_exist_archives.append(archive_dir)

        # EXECUTE
        backup_mgmt.archive_directory(
            target_worlds,
            archive_directories_fs_setup,
            suffix,
            max_archives,
        )

        # ASSERT
        num_archives = len(list(expected_archive_path.iterdir()))
        assert (
            num_archives == archives_to_premake + 1
        ), f"Expected there to be a max of '{archives_to_premake + 1}' archive directories but found '{num_archives}'!"

        for archive in should_exist_archives:
            assert (
                archive.exists()
            ), f"Expected a premade archive directory '{expected_archive_path}' to exist but it didn't!"

    def test__archive_directory__success(
        self,
        mocker: MockerFixture,
        target_worlds: List[str],
        archive_directories_fs_setup: Path,
        backup_mgmt: BackupManagement,
        world_file: str,
    ):
        """Tests that the target dir to archive gets archived as expected"""

        # SETUP
        time_time = 123456789
        mocker.patch("time.time", return_value=time_time)

        suffix = "_testsuffix"
        expected_archive_path = Path(f"{archive_directories_fs_setup}{suffix}")
        expected_archive_instance_path = (
            expected_archive_path / f"{archive_directories_fs_setup.name}-{time_time}"
        )
        max_archives = 10

        expected_files = []
        expected_dirs = []
        for target_world in target_worlds:
            expected_dir_path = expected_archive_instance_path / target_world
            expected_dirs.append(expected_dir_path)
            expected_file_path = expected_dir_path / world_file
            expected_files.append(expected_file_path)

        non_target_world_path = archive_directories_fs_setup / "NotATargetWorld"
        non_target_world_path.mkdir(exist_ok=True, parents=True)
        non_target_file_in_world = non_target_world_path / world_file
        non_target_file_in_world.touch()

        # EXECUTE
        backup_mgmt.archive_directory(
            target_worlds,
            archive_directories_fs_setup,
            suffix,
            max_archives,
        )

        # ASSERT
        for directory in expected_dirs:
            assert (
                directory.exists()
            ), f"Expected an archive directory '{directory}' to exist but it didn't!"

        for file in expected_files:
            assert (
                file.exists()
            ), f"Expected an archived file '{file}' to exist but it didn't!"

        assert (
            non_target_world_path.exists()
        ), f"Expected a non-target world to have remained untouched in original location!"

        assert (
            non_target_file_in_world.exists()
        ), f"Expected a non-target file to have remained untouched in original location!"

    def test__build_restore_minecraft_restic_command__success(
        self,
        backup_mgmt: BackupManagement,
        restic_target_id: str,
        target_worlds: List[str],
    ):
        # SETUP
        # EXECUTE
        command = backup_mgmt.build_restore_minecraft_restic_command(
            restic_target_id, target_worlds
        )

        # ASSERT
        assert (
            restic_target_id in command
        ), "Expected restic target id to be included in the command!"

        for world in target_worlds:
            assert (
                world in command
            ), "Expected all supplied target worlds to be in the command!"

    def test__restore_minecraft__cannot_restore_while_container_up_error(
        self,
        backup_mgmt: BackupManagement,
        env1_object: Env,
        world_group: str,
        restic_target_id: str,
        target_worlds: List[str],
        bypass_running_container_restriction: bool,
    ):
        """Ensure we get an error if the container we're trying to restore to is currently running."""

        # SETUP
        backup_mgmt.docker_management.is_container_up.side_effect = [True]

        with pytest.raises(CannotRestoreWhileContainerUpError):
            # EXECUTE
            # ASSERT
            backup_mgmt.restore_minecraft(
                env1_object,
                world_group,
                restic_target_id,
                target_worlds,
                bypass_running_container_restriction,
            )

    def test__restore_minecraft__restore_already_in_progress_error(
        self,
        backup_mgmt: BackupManagement,
        env1_object: Env,
        world_group: str,
        restic_target_id: str,
        target_worlds: List[str],
        bypass_running_container_restriction: bool,
    ):
        """Ensure we get an error if there is a restore already in progress for this world group and env."""

        # SETUP
        backup_mgmt.docker_management.is_container_up.side_effect = [False, True]

        with pytest.raises(RestoreAlreadyInProgressError):
            # EXECUTE
            # ASSERT
            backup_mgmt.restore_minecraft(
                env1_object,
                world_group,
                restic_target_id,
                target_worlds,
                bypass_running_container_restriction,
            )

    def test__restore_minecraft__success(
        self,
        mocker: MockerFixture,
        backup_mgmt: BackupManagement,
        env1_object: Env,
        world_group: str,
        restic_target_id: str,
        target_worlds: List[str],
        bypass_running_container_restriction: bool,
    ):
        """Ensures given no container state issues, the docker call to run the restore sidecar container is executed"""

        # SETUP
        backup_mgmt.docker_management.is_container_up.side_effect = [False, False]
        backup_mgmt.docker_client.containers.run.return_value = ""
        mocker.patch(
            "src.api.lib.backup_management.BackupManagement.archive_directory",
            return_value=None,
        )

        # EXECUTE
        backup_mgmt.restore_minecraft(
            env1_object,
            world_group,
            restic_target_id,
            target_worlds,
            bypass_running_container_restriction,
        )

        # ASSERT
        backup_mgmt.docker_client.containers.run.assert_called_once()
