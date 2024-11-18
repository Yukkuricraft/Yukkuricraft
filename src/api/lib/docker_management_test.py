from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest.mock import PropertyMock, call
import pytest  # type: ignore

from pydantic import ValidationError  # type: ignore
from src.api.lib.docker_management import (
    DockerManagement,
    convert_docker_compose_container_to_legacy_defined_container,
    convert_dockerpy_container_to_legacy_active_container,
)
from src.common.config.config_node import ConfigNode
from src.common.constants import (
    YC_CONTAINER_NAME_LABEL,
    YC_CONTAINER_TYPE_LABEL,
    YC_ENV_LABEL,
)
from src.common.environment import Env  # type: ignore


@pytest.fixture
def docker_mgmt(mocker) -> DockerManagement:
    mock_docker_client = mocker.MagicMock()
    return DockerManagement(client=mock_docker_client)


@pytest.fixture
def name():
    return "A Name"


@pytest.fixture
def created():
    return "Created at Timestamp"


@pytest.fixture
def id():
    return "An Id String"


@pytest.fixture
def config_labels():
    return {
        "LabelName1": "LabelValue1",
        "Label.Name.2": "Label.Value.2",
        "com.docker.compose.service": "docker compose service",
        YC_CONTAINER_NAME_LABEL: "yc-container-name",
        YC_CONTAINER_TYPE_LABEL: "minecraft",
    }


@pytest.fixture
def config_hostname():
    return "A hostname"


@pytest.fixture
def config_cmd():
    return "A Command"


@pytest.fixture
def config_entrypoint():
    return "An Entrypoint"


@pytest.fixture
def config_image():
    return "An Image"


@pytest.fixture
def config_network_settings():
    return {
        "Networks": {
            "Key1": "Val1",
            "Key2": "Val2",
        },
    }


@pytest.fixture
def config_exposed_ports():
    return {
        "PortKey1": "PortVal1",
        "PortKey2": "PortVal2",
    }


@pytest.fixture
def state_status():
    return "A Status"


@pytest.fixture
def state_started_at():
    return "1970-01-01T01:23:45.123456789Z"


@pytest.fixture
def state_health():
    return {
        "Status": "Health Status",
    }


@pytest.fixture
def mounts():
    return [
        {
            "Source": "source1",
            "Destination": "dest1",
        },
        {
            "Source": "source2",
            "Destination": "dest2",
        },
    ]


@pytest.fixture
def docker_container_fields(
    name,
    created,
    id,
    config_labels,
    config_hostname,
    config_cmd,
    config_entrypoint,
    config_image,
    config_network_settings,
    config_exposed_ports,
    state_status,
    state_started_at,
    state_health,
    mounts,
):
    return {
        "Name": name,
        "Created": created,
        "Id": id,
        "Config": {
            "Labels": config_labels,
            "Hostname": config_hostname,
            "Cmd": config_cmd,
            "Entrypoint": config_entrypoint,
            "Image": config_image,
            "NetworkSettings": config_network_settings,
            "ExposedPorts": config_exposed_ports,
        },
        "State": {
            "Status": state_status,
            "StartedAt": state_started_at,
            "Health": state_health,
        },
        "Mounts": mounts,
    }


@pytest.fixture
def docker_container(mocker, docker_container_fields):
    container = mocker.MagicMock()
    container.attrs = docker_container_fields
    container.labels = container.attrs["Config"]["Labels"]
    container.name = container.attrs["Name"]
    return container


@pytest.fixture
def docker_network_name():
    return "yc-network-name"


@pytest.fixture
def docker_ports():
    return ["123:321", "1337:7331"]


@pytest.fixture
def container_config_node(
    name,
    config_image,
    config_hostname,
    mounts,
    docker_network_name,
    docker_ports,
    config_labels,
):
    config_labels[YC_ENV_LABEL] = "${ENV}"
    return ConfigNode(
        {
            "name": name,
            "image": config_image,
            "container_name": name,
            "hostname": config_hostname,
            "mounts": [], # TODO: It's not actually the 'mounts' attr... we don't return anything on these atm.
            "networks": [docker_network_name],
            "ports": docker_ports,
            "labels": config_labels,
        }
    )


@pytest.fixture
def success_exit_code():
    return 200


@pytest.fixture
def success_exec_run_output():
    return ("A successful stdout string", "A successful stderr string")


@pytest.fixture
def extra_exec_run_args():
    return {
        "extraarg1": "extraargval1",
        "extraarg2": "extraargval2",
    }


@pytest.fixture
def env_name():
    return "An Env Name"


class TestDockerManagement:
    """Docker Management lib unit tests"""

    def test__convert_dockerpy_container_to_container_definition__success(
        self,
        docker_container,
        config_cmd,
        config_hostname,
        created,
        id,
        config_image,
        config_labels,
        mounts,
        config_network_settings,
        config_exposed_ports,
        state_status,
    ):
        """Ensures given a mock docker container object, we convert it to the LegacyContainerDefinition shape with the correct values parsed out."""
        container_def = convert_dockerpy_container_to_legacy_active_container(
            docker_container
        )

        names = [
            config_labels[YC_CONTAINER_NAME_LABEL],  # Name we defined
            config_labels[
                "com.docker.compose.service"
            ],  # Name defined by docker service
            config_hostname,  # Hostname of the container
        ]
        networks = list(config_network_settings.get("Networks").keys())
        ports = list(config_exposed_ports.keys())
        mounts_formatted = list(
            map(lambda d: f"{d['Source']}:{d['Destination']}", mounts)
        )

        assert (
            container_def.Command == config_cmd
        ), f"Expected 'Command' field to have value '{config_cmd}'!"

        assert (
            container_def.ContainerName == config_hostname
        ), f"Expected 'ContainerName' field to have value '{config_hostname}'!"

        assert (
            container_def.CreatedAt == created
        ), f"Expected 'CreatedAt' field to have value '{created}'!"

        assert (
            container_def.Hostname == config_hostname
        ), f"Expected 'Hostname' field to have value '{config_hostname}'!"

        assert container_def.ID == id, f"Expected 'Id' field to have value '{id}'!"

        assert (
            container_def.Image == config_image
        ), f"Expected 'Image' field to have value '{config_image}'!"

        assert (
            container_def.Labels == config_labels
        ), f"Expected 'Labels' field to have value '{config_labels}'!"

        assert (
            container_def.Mounts == mounts_formatted
        ), f"Expected 'Mounts' field to have value '{mounts_formatted}'!"

        assert (
            container_def.Names == names
        ), f"Expected 'Names' field to have value '{names}'!"

        assert (
            container_def.Networks == networks
        ), f"Expected 'Networks' field to have value '{networks}'!"

        assert (
            container_def.Ports == ports
        ), f"Expected 'Ports' field to have value '{ports}'!"

        assert (
            container_def.State == state_status
        ), f"Expected 'State' field to have value '{state_status}'"

    def test__convert_docker_compose_container_to_container_definition__success(
        self, mocker, container_config_node, env_name
    ):
        env_mock = mocker.MagicMock()
        env_mock.name = env_name

        container = convert_docker_compose_container_to_legacy_defined_container(
            container_config_node.name,
            container_config_node,
            env_mock,
        )
        assert (
            container.image == container_config_node.image
        ), f"Expected 'image' field to contain '{container_config_node.image}'!"
        assert (
            container.names == [ container_config_node.name, container_config_node.name ]
        ), f"Did not get the expected 'names' field value!"
        assert (
            container.container_name == container_config_node.container_name
        ), f"Expected 'container_name' field to contain '{container_config_node.container_name}'!"
        assert (
            container.hostname == container_config_node.hostname
        ), f"Expected 'hostname' field to contain '{container_config_node.hostname}'!"
        assert (
            container.mounts == container_config_node.mounts
        ), f"Expected 'mounts' field to contain '{container_config_node.mounts}'!"
        assert (
            container.networks == container_config_node.networks
        ), f"Expected 'networks' field to contain '{container_config_node.networks}'!"
        assert (
            container.ports == container_config_node.ports
        ), f"Expected 'ports' field to contain '{container_config_node.ports}'!"

    def test__pty_attach_container__success(
        self, mocker, docker_container, docker_mgmt: DockerManagement
    ):
        """Ensures the function calls the PtyProcessUnicode.spawn() method with the docker attach command."""
        spawn_mock = mocker.patch(
            "src.api.lib.docker_management.PtyProcessUnicode.spawn"
        )
        docker_mgmt.pty_attach_container(docker_container)

        expected_call_args = call(
            ["docker", "attach", docker_container.name],
        )
        assert (
            spawn_mock.call_args_list[0] == expected_call_args
        ), "Did not get the expected calls to PtyProcessUnicode.spawn()!"

    def test__exec_run__args_correct_no_extras(
        self,
        docker_container,
        docker_mgmt: DockerManagement,
        config_cmd: str,
        success_exit_code: int,
        success_exec_run_output: Tuple[str, str],
    ):
        """Ensures exec_run() calls the docker container's exec_run() with expected args."""
        docker_container.exec_run.return_value = (
            success_exit_code,
            success_exec_run_output,
        )

        status_code, output = docker_mgmt.exec_run(docker_container, config_cmd)

        expected_call_args = call(
            cmd=config_cmd,
            demux=True,
        )
        assert (
            docker_container.exec_run.call_args_list[0] == expected_call_args
        ), "Did not get the expected args to container.exec_run()!"
        assert (
            status_code == success_exit_code
        ), f"Expected output from exec_run() to be '{success_exit_code}'!"
        assert output == "\n".join(
            success_exec_run_output
        ), f"Expected output from exec_run() to be '{success_exec_run_output}'!"

    def test__exec_run__args_correct_w_extras(
        self,
        docker_container,
        docker_mgmt: DockerManagement,
        config_cmd: str,
        extra_exec_run_args: Dict[str, str],
        success_exit_code: int,
        success_exec_run_output: Tuple[str, str],
    ):
        """Ensures exec_run() calls the docker container's exec_run() with expected args."""

        docker_container.exec_run.return_value = (
            success_exit_code,
            success_exec_run_output,
        )

        status_code, output = docker_mgmt.exec_run(
            docker_container, config_cmd, False, **extra_exec_run_args
        )

        args = {"cmd": config_cmd, "demux": True, **extra_exec_run_args}
        assert docker_container.exec_run.call_args_list[0] == call(
            **args
        ), "Did not get the expected args to container.exec_run()!"
        assert (
            status_code == success_exit_code
        ), f"Expected output from exec_run() to be '{success_exit_code}'!"
        assert output == "\n".join(
            success_exec_run_output
        ), f"Expected output from exec_run() to be '{success_exec_run_output}'!"

    def test__send_command_to_container__success(
        self,
        mocker,
        docker_container,
        docker_mgmt: DockerManagement,
        config_cmd: str,
        success_exit_code,
    ):
        """Tests that the `perform_cb_on_container()` method is called with expected args for container name and the rcon-cli commands."""
        exec_run_return_value = "An exec_run() Return Value"
        exec_run_mock = mocker.patch(
            "src.api.lib.docker_management.DockerManagement.exec_run",
            return_value=(success_exit_code, exec_run_return_value),
        )
        perform_cb_on_container_spy = mocker.spy(docker_mgmt, "perform_cb_on_container")

        out = docker_mgmt.send_command_to_container(docker_container.name, config_cmd)

        assert (
            exec_run_return_value == out
        ), f"Expected output from send_command_to_container to be '{exec_run_return_value}'!"
        assert (
            perform_cb_on_container_spy.call_args_list[0][1]["container_name"]
            == docker_container.name
        )
        assert exec_run_mock.call_args_list[0][0][1] == ["rcon-cli", config_cmd]

    def test__prepare_container_for_ws_attach__success(
        self, mocker, docker_container, docker_mgmt: DockerManagement
    ):
        """Ensures we call the pty_attach_container() helper with a container we get from container_name_to_container()"""
        container_name_to_container_return_value = mocker.MagicMock()
        container_name_to_container_mock = mocker.patch(
            "src.api.lib.docker_management.DockerManagement.container_name_to_container",
            return_value=container_name_to_container_return_value,
        )
        pty_attach_container_spy = mocker.spy(docker_mgmt, "pty_attach_container")

        docker_mgmt.prepare_container_for_ws_attach(docker_container.name)

        assert container_name_to_container_mock.call_args_list[0][0] == (
            docker_container.name,
        ), f"Expected call to container_name_to_container() to include the container name '{docker_container.name}'!"
        assert pty_attach_container_spy.call_args_list[0][0] == (
            container_name_to_container_return_value,
        ), "Expected call to pty_attach_container() to include the container mock object"

    def test__container_name_to_container__success(
        self, docker_container, docker_mgmt: DockerManagement
    ):
        """Ensure we correctly dockerpy's containers.get() method with the container name."""
        docker_mgmt.client.containers.get.return_value = docker_container
        container = docker_mgmt.container_name_to_container(docker_container.name)

        assert (
            container == docker_container
        ), f"Did not get the expected container from container_name_to_container()!"

    def test__is_container_up__each_status_returns_expected_bool(
        self, mocker, docker_container, docker_mgmt: DockerManagement
    ):
        """Ensures is_container_up() returns the correct bool for each possible docker container status."""
        status_mappings = {
            "created": True,
            "restarting": True,
            "running": True,
            "removing": False,
            "paused": False,
            "exited": False,
            "dead": False,
        }

        for status, expected_is_up in status_mappings.items():
            docker_container.status = status
            mocker.patch(
                "src.api.lib.docker_management.DockerManagement.container_name_to_container",
                return_value=docker_container,
            )
            is_up = docker_mgmt.is_container_up(docker_container.name)

            assert (
                is_up == expected_is_up
            ), f"Expected is_container_up() to return {expected_is_up}!"

    def test__list_defined_containers(self):
        pass

    def test__list_active_containers(self):
        pass

    def test__perform_cb_on_container(self):
        pass

    def test__up_one_container(self):
        pass

    def test__down_one_container(self):
        pass

    def test__restart_one_container(self):
        pass

    def test__up_containers(self):
        pass

    def test__down_containers(self):
        pass

    def test__restart_containers(self):
        pass
