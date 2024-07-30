# Prerequisites:
# Setup SSH proxy jump
# Install or enable Docker on the remote machine (is pre-installed on PLCs with firmware versions above 20)
# Add user to the docker group: "sudo usermod -aG docker $USER"
# enable experimental features for Docker on your local machine (Docker Desktop -> Preferences -> Docker Engine) to be able to build the docker-compose image for the right platform.
# OPTIONAL: This shouldn't happen, but if you encounter: 'exec /usr/bin/docker-compose: exec format error', you might need to enable qemu:
# run: 'docker run --rm --privileged multiarch/qemu-user-static --reset -p yes'

import subprocess
import tempfile
import time
from paramiko import SSHClient
from scp import SCPClient
import os
from energy_box_control.custom_logging import get_logger
from contextlib import contextmanager
import os


logger = get_logger(__name__)
logger.setLevel("DEBUG")

HOST_NAME = "power-hub-plc"
SSH_USER = "admin"
REMOTE_HOME_DIR = f"/home/{SSH_USER}"
PASSWORD_ENV_NAME = "POWER_HUB_PLC_PASSWORD"
PAGERDUTY_KEY_ENV_NAME = "PAGERDUTY_CONTROL_APP_KEY"
CLOUD_VERNEMQ_ENV_NAME = ""
MQTT_PASSWORD_ENV_NAME = "PLC_MQTT_PASSWORD"
REMOTE_DOCKER_COMPOSE_DIR = os.path.join(REMOTE_HOME_DIR, "plc-docker-compose")
DOCKER_COMPOSE_IMAGE_NAME = "plc-docker-compose:latest-armv7"


@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


@contextmanager
def ssh_client():
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect(
        hostname=HOST_NAME, username=SSH_USER, password=os.getenv(PASSWORD_ENV_NAME)
    )
    logger.debug("SSH connected")
    try:
        yield ssh
    finally:
        ssh.close()


def blocking_command(client: SSHClient, command: str):
    stdin, stdout, stderr = client.exec_command(command)
    _ = stdout.channel.recv_exit_status()
    error = "".join((line for line in iter(stderr.readline, "")))
    if error:
        logger.error(error)
    return "".join((line for line in iter(stdout.readline, "")))


def build_for_arch(
    image_name: str,
    dockerfile: str,
    platform: str = "linux/arm/v7",
    no_cache: bool = True,
):
    build_docker_compose_commands = [
        arg
        for arg in [
            "docker",
            "buildx",
            "build",
            "--no-cache" if no_cache else None,
            "--platform",
            platform,
            "--tag",
            image_name,
            "-f",
            dockerfile,
            "--output",
            "type=docker",
            ".",
        ]
        if arg
    ]

    logger.debug(
        f"Building docker-compose image with command '{" ".join(build_docker_compose_commands)}'"
    )
    subprocess.run(build_docker_compose_commands)


def save_docker_image(folder: str, image_name: str):
    docker_compose_local_image_path = os.path.join(folder, "image.tar")
    logger.debug(f"Saving docker image to {docker_compose_local_image_path}")
    subprocess.run(
        ["docker", "save", "-o", docker_compose_local_image_path, image_name]
    )
    return docker_compose_local_image_path


def add_docker_image_on_remote(ssh: SSHClient, image_path: str):
    logger.debug("Adding docker image on the remote")
    blocking_command(ssh, f"docker load -i {image_path}")


def copy_file_to_remote(
    ssh: SSHClient, path: str, destination_path: str = REMOTE_HOME_DIR
):
    with SCPClient(ssh.get_transport()) as scp:  # type: ignore
        logger.debug(f"Copying {path} to {destination_path}")
        scp.put(path, destination_path)
    return os.path.join(destination_path, os.path.basename(path))


def remove_file_on_remote(ssh: SSHClient, path: str):
    logger.debug("Cleaning up on remote")
    blocking_command(
        ssh,
        f"rm {path}",
    )


def add_compose_alias_to_profile(ssh):
    stdout = blocking_command(
        ssh,
        f"cat {os.path.join(REMOTE_HOME_DIR, ".profile")}",  # is this the right file on the PLC?
    )

    if not "alias docker-compose" in stdout:
        logger.debug("Adding alias to .profile")
        alias_command = f"alias docker-compose='docker run --platform linux/arm/v7 --rm -t --privileged -v $(pwd):/compose -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker {DOCKER_COMPOSE_IMAGE_NAME}'"
        blocking_command(
            ssh,
            f'echo "{alias_command}" >> {os.path.join(REMOTE_HOME_DIR, ".profile")}',
        )


def build_and_push_docker_compose():

    build_for_arch(
        DOCKER_COMPOSE_IMAGE_NAME,
        os.path.join(os.getcwd(), "plc-docker-compose.Dockerfile"),
    )
    with tempfile.TemporaryDirectory() as tmpdirname:
        docker_compose_local_image_path = save_docker_image(
            tmpdirname, DOCKER_COMPOSE_IMAGE_NAME
        )

        with ssh_client() as ssh:
            remote_image_path = copy_file_to_remote(
                ssh, docker_compose_local_image_path
            )
            add_docker_image_on_remote(ssh, remote_image_path)
            remove_file_on_remote(ssh, remote_image_path)
            add_compose_alias_to_profile(
                ssh
            )  # not necessary for the script, handy for manual use.


def build_and_push_vernemq():
    vernemq_image_name = "vernemq:latest-armv7"
    with cwd("vernemq"):
        build_for_arch(
            vernemq_image_name,
            os.path.join(os.getcwd(), "vernemq.Dockerfile"),
            no_cache=False,
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            docker_local_image_path = save_docker_image(tmpdirname, vernemq_image_name)

            with ssh_client() as ssh:
                remote_image_path = copy_file_to_remote(ssh, docker_local_image_path)
                add_docker_image_on_remote(ssh, remote_image_path)
                remove_file_on_remote(ssh, remote_image_path)


def build_and_push_control_app():
    control_app_image_name = "python-control-app:latest-armv7"
    build_for_arch(
        control_app_image_name, os.path.join(os.getcwd(), "python_control.Dockerfile")
    )
    with tempfile.TemporaryDirectory() as tmpdirname:
        docker_local_image_path = save_docker_image(tmpdirname, control_app_image_name)

        with ssh_client() as ssh:
            remote_image_path = copy_file_to_remote(ssh, docker_local_image_path)
            add_docker_image_on_remote(ssh, remote_image_path)
            remove_file_on_remote(ssh, remote_image_path)


def copy_docker_compose_file_to_plc():
    logger.debug("Starting with copying docker compose file to plc")

    local_file_path = "plc.docker-compose.yml"
    remote_file_path = os.path.join(REMOTE_DOCKER_COMPOSE_DIR, "docker-compose.yml")

    with ssh_client() as ssh:
        logger.debug(f"Creating directory {os.path.dirname(remote_file_path)}")
        blocking_command(ssh, f"mkdir {os.path.dirname(remote_file_path)}")
        copy_file_to_remote(ssh, local_file_path, remote_file_path)


def create_env_file():
    with ssh_client() as ssh:
        envs = [
            ("MQTT_PASSWORD", os.getenv(MQTT_PASSWORD_ENV_NAME)),
            ("CLOUD_VERNEMQ_URL", os.getenv(CLOUD_VERNEMQ_ENV_NAME)),
            ("PAGERDUTY_CONTROL_APP_KEY", os.getenv(PAGERDUTY_KEY_ENV_NAME)),
            ("MQTT_HOST", "vernemq"),
        ]
        remote_env_path = os.path.join(REMOTE_DOCKER_COMPOSE_DIR, ".env")
        stdout = blocking_command(ssh, f"cat {remote_env_path}")
        if not stdout:
            blocking_command(ssh, f"touch {remote_env_path}")
        for env_name, env_value in envs:
            if not env_name in stdout:
                blocking_command(
                    ssh,
                    f"echo {env_name}={env_value} >> {remote_env_path}",
                )


def run_docker_compose():
    with ssh_client() as ssh:
        docker_compose_alias = f"docker run --rm -t --privileged -v {REMOTE_HOME_DIR}:/compose -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker {DOCKER_COMPOSE_IMAGE_NAME}"
        compose_command = f"{docker_compose_alias} -f {os.path.basename(REMOTE_DOCKER_COMPOSE_DIR)}/docker-compose.yml up -d control"
        logger.debug(f"Running '{compose_command}'")
        blocking_command(ssh, compose_command)
        logger.debug("Done running compose command")


if __name__ == "__main__":
    start = time.time()
    build_and_push_docker_compose()
    build_and_push_vernemq()
    build_and_push_control_app()
    copy_docker_compose_file_to_plc()
    create_env_file()
    run_docker_compose()
    stop = time.time()
    logger.debug(f"Script took {stop - start} seconds.")
