# Prerequisites:
# Setup SSH proxy jump
# Install Docker om the remote machine (is pre-installed on PLCs with firmware versions above 20)
# Be able to download Docker images locally
# Add user to the docker group? "sudo usermod -aG docker $USER"

from dataclasses import dataclass
import subprocess
import tempfile
import time
from paramiko import SSHClient
from scp import SCPClient
import os
from energy_box_control.custom_logging import get_logger

logger = get_logger(__name__)
logger.setLevel("DEBUG")

HOST_NAME = "power-hub-plc-testing"
SSH_USER = "sietse_huisman"
REMOTE_HOME_DIR = "/home/sietse_huisman"
PASSWORD_ENV_NAME = "POWER_HUB_PLC_TESTING_PASSWORD"
PAGERDUTY_KEY_ENV_NAME = "PAGERDUTY_SIMULATION_KEY"
CLOUD_VERNEMQ_ENV_NAME = ""
MQTT_PASSWORD_ENV_NAME = "PLC_MQTT_PASSWORD"
GCLOUD_PROJECT_LOCATION = "europe-west1"
GCLOUD_PROJECT_ID = "power-hub-423312"
GCLOUD_REPOSITORY = "power-hub"
REMOTE_DOCKER_COMPOSE_DIR = os.path.join(REMOTE_HOME_DIR, "plc-docker-compose")


from contextlib import contextmanager
import os


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
    return "".join([line for line in iter(stdout.readline, "")])


def download_and_push_docker_compose():
    local_docker_file_path = "plc.Dockerfile"
    remote_docker_compose_dir = os.path.join(REMOTE_HOME_DIR, "docker-compose")
    with ssh_client() as ssh:
        blocking_command(ssh, f"mkdir {remote_docker_compose_dir}")
        with SCPClient(ssh.get_transport()) as scp:  # type: ignore
            logger.debug("Copying Dockerfile to remote")
            scp.put(
                local_docker_file_path,
                os.path.join(remote_docker_compose_dir, "Dockerfile"),
            )
        image_tag = "docker-compose"
        docker_build_command = (
            f"docker build -t {image_tag} {remote_docker_compose_dir}"
        )
        logger.debug("Building docker compose image")
        logger.debug(docker_build_command)
        blocking_command(ssh, docker_build_command)
        blocking_command(ssh, f"rm -rf {remote_docker_compose_dir}")
        stdout = blocking_command(
            ssh, f"cat {os.path.join(REMOTE_HOME_DIR, ".profile")}"
        )
        if not "alias docker-compose" in stdout:
            logger.debug("Adding alias to .profile")
            alias_command = f"alias docker-compose='docker run --rm -t --privileged -v $(pwd):/compose -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker {image_tag}'"
            blocking_command(
                ssh,
                f'echo "{alias_command}" >> {os.path.join(REMOTE_HOME_DIR, ".profile")}',
            )


def python_app_image():
    logger.debug("tarring energy_box_control folder")
    tar_name = "energy_box.tar.gz"
    python_app_dockerfile = "python_script.Dockerfile"
    toml = "pyproject.toml"
    lock_file = "poetry.lock"
    image_tag = f"{GCLOUD_PROJECT_LOCATION}-docker.pkg.dev/{GCLOUD_PROJECT_ID}/{GCLOUD_REPOSITORY}/python-app"
    energy_box_control_remote_dir = os.path.join(REMOTE_HOME_DIR, "energy-box-control")
    subprocess.run(["tar", "czf", tar_name, "energy_box_control"])
    with ssh_client() as ssh:
        logger.debug(f"Creating {energy_box_control_remote_dir}")
        blocking_command(ssh, f"mkdir {energy_box_control_remote_dir}")
        with SCPClient(ssh.get_transport()) as scp:  # type: ignore
            logger.debug(f"Copying {tar_name} to {energy_box_control_remote_dir}")
            scp.put(tar_name, energy_box_control_remote_dir)
            scp.put(python_app_dockerfile, energy_box_control_remote_dir)
            scp.put(toml, energy_box_control_remote_dir)
            scp.put(lock_file, energy_box_control_remote_dir)
        logger.debug("Unzipping tar")
        blocking_command(
            ssh,
            f"tar -xf {os.path.join(energy_box_control_remote_dir, tar_name)} -C {energy_box_control_remote_dir}",
        )
        docker_build_command = f"docker build --platform linux/amd64 --tag '{image_tag}' {energy_box_control_remote_dir} -f {os.path.join(energy_box_control_remote_dir, "python_script.Dockerfile")}"
        logger.debug(f"Running '{docker_build_command}'")
        blocking_command(ssh, docker_build_command)
    subprocess.run(["rm", tar_name])


def download_and_push_docker_container(image_name: str):
    with tempfile.TemporaryDirectory() as tmpdirname:
        docker_image_local_file_path = os.path.join(tmpdirname, "image.tar")
        logger.debug(f"Changing to dir {tmpdirname}")
        with cwd(tmpdirname):
            subprocess.run(["docker", "pull", image_name])
            logger.debug(f"Saving image to {docker_image_local_file_path}")
            subprocess.run(
                ["docker", "save", "-o", docker_image_local_file_path, image_name]
            )
            with ssh_client() as ssh:
                with SCPClient(ssh.get_transport()) as scp:  # type: ignore
                    logger.debug(
                        f"Copying {docker_image_local_file_path} to {REMOTE_HOME_DIR}"
                    )
                    scp.put(docker_image_local_file_path, REMOTE_HOME_DIR)
                logger.debug("Adding docker image on the remote")
                blocking_command(
                    ssh,
                    f"docker load -i {os.path.join(REMOTE_HOME_DIR, os.path.basename(docker_image_local_file_path))}",
                )
                logger.debug("Removing docker image tar file on the remote")
                blocking_command(
                    ssh,
                    f"rm {os.path.join(REMOTE_HOME_DIR, os.path.basename(docker_image_local_file_path))}",
                )


def copy_docker_compose_file_to_plc():
    logger.debug("Starting with copying docker compose file to plc")

    local_file_path = "plc.docker-compose.yml"
    remote_file_path = os.path.join(REMOTE_DOCKER_COMPOSE_DIR, "docker-compose.yml")

    with ssh_client() as ssh:
        logger.debug(f"Creating directory {os.path.dirname(remote_file_path)}")
        blocking_command(ssh, f"mkdir {os.path.dirname(remote_file_path)}")
        with SCPClient(ssh.get_transport()) as scp:  # type: ignore
            logger.debug(
                f"Copying {local_file_path} to {os.path.dirname(remote_file_path)}"
            )
            scp.put(f"{local_file_path}", remote_file_path)


def create_env_file():
    with ssh_client() as ssh:
        envs = [
            ("MQTT_PASSWORD", os.getenv(MQTT_PASSWORD_ENV_NAME)),
            ("CLOUD_VERNEMQ_URL", os.getenv(CLOUD_VERNEMQ_ENV_NAME)),
            ("PAGERDUTY_SIMULATION_KEY", os.getenv(PAGERDUTY_KEY_ENV_NAME)),
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
        docker_compose_alias = f"docker run --rm -t --privileged -v {REMOTE_HOME_DIR}:/compose -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker docker-compose"
        compose_command = f"{docker_compose_alias} -f {os.path.basename(REMOTE_DOCKER_COMPOSE_DIR)}/docker-compose.yml up -d control"
        logger.debug(f"Running '{compose_command}'")
        blocking_command(ssh, compose_command)
        logger.debug("Done running compose command")


if __name__ == "__main__":
    start = time.time()
    download_and_push_docker_compose()
    # python_app_image()
    download_and_push_docker_container(
        f"{GCLOUD_PROJECT_LOCATION}-docker.pkg.dev/{GCLOUD_PROJECT_ID}/{GCLOUD_REPOSITORY}/python-app"
    )
    copy_docker_compose_file_to_plc()
    create_env_file()
    run_docker_compose()
    stop = time.time()
    logger.debug(f"Script took {stop - start} seconds.")
