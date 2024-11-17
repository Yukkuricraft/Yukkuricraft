from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import PropertyMock, call
import pytest  # type: ignore

from pydantic import ValidationError  # type: ignore
from src.api.lib.docker_management import (
    DockerManagement,
    convert_dockerpy_container_to_container_definition,
)
from src.common.constants import YC_CONTAINER_NAME_LABEL, YC_CONTAINER_TYPE_LABEL
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
        container_def = convert_dockerpy_container_to_container_definition(
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

    def test__pty_attach_container(
        self, mocker, docker_container, docker_mgmt: DockerManagement, name
    ):
        spawn_mock = mocker.patch(
            "src.api.lib.docker_management.PtyProcessUnicode.spawn"
        )
        docker_mgmt.pty_attach_container(docker_container)

        expected_call_args = call(
            ["docker", "attach", docker_container.name],
        )
        assert (
            spawn_mock.call_args_list[0] == expected_call_args
        ), f"Expected call args to be PtyProcessUnicode.spawn(\"{'\", \"'.join(expected_call_args[0])}\")"

    def test__exec_run(self):
        pass

    def test__send_command_to_container(self):
        pass

    def test__prepare_container_for_ws_attach(self):
        pass

    def test__container_name_to_container(self):
        pass

    def test__is_container_up(self):
        pass

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
