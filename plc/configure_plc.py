import subprocess
import tempfile
import time
from paramiko import AutoAddPolicy, SSHClient
from scp import SCPClient
import os
from energy_box_control.custom_logging import get_logger
from contextlib import contextmanager
import os


logger = get_logger(__name__)
logger.setLevel("DEBUG")

REMOTE_DIR = f"/home/admin/docker-files"
REMOTE_DOCKER_COMPOSE_DIR = os.path.join(REMOTE_DIR, "plc-docker-compose")
DOCKER_COMPOSE_IMAGE_NAME = "plc-docker-compose:latest-armv7"

REMOTE_DOCKER_COMPOSE_DIR_ENV_NAME = "REMOTE_DOCKER_COMPOSE_DIR"
PAGERDUTY_KEY_ENV_NAME = "PAGERDUTY_CONTROL_APP_KEY"
CLOUD_VERNEMQ_ENV_NAME = "PROD_VERNEMQ_URL"
MQTT_PASSWORD_ENV_NAME = "PROD_MQTT_PASSWORD"


configs = {
    "wireguard": {
        "hostname": "wireguard.foundationzero.org",
        "username": "<user>",
        "key_path": "<path>/<to>/.ssh/id_rsa",
        "next_host": "10.0.2.20",
    },
    "pi": {
        "hostname": "10.0.2.20",
        "username": "pi",
        "password": os.getenv("POWER_HUB_PASSWORD"),
        "next_host": "192.168.1.15",
    },
    "plc": {
        "hostname": "192.168.1.15",
        "username": "root",
        "password": os.getenv("POWER_HUB_PLC_PASSWORD"),
    },
}


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

    clients = []
    prev_sock = None

    try:
        for _, config in configs.items():
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())
            connect_kwargs = {
                "hostname": config["hostname"],
                "username": config["username"],
                **(
                    {"key_filename": config["key_filename"]}
                    if "key_filename" in config
                    else {}
                ),
                **({"password": config["password"]} if "password" in config else {}),
                **({"sock": prev_sock} if prev_sock else {}),
            }
            client.connect(**connect_kwargs)
            clients.append(client)
            if "next_host" in config:
                prev_sock = client.get_transport().open_channel(  # type: ignore
                    "direct-tcpip", (config["next_host"], 22), ("", 0)
                )

        client = clients[-1]
        _, stdout, _ = client.exec_command("whoami")
        logger.debug(f"Logged in as: {stdout.read().decode()}")
        yield client

    finally:
        for client in reversed(clients):
            client.close()


def blocking_command(client: SSHClient, command: str):
    _, stdout, stderr = client.exec_command(command, timeout=None)
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


def save_docker_image(folder: str, image_name: str, tar_name: str = "image.tar"):
    docker_compose_local_image_path = os.path.join(folder, tar_name)
    commands = ["docker", "save", "-o", docker_compose_local_image_path, image_name]
    logger.debug(f"Saving docker image to with command '{" ".join(commands)}'")
    subprocess.run(
        ["docker", "save", "-o", docker_compose_local_image_path, image_name]
    )
    return docker_compose_local_image_path


def add_docker_image_on_remote(ssh: SSHClient, image_path: str):
    logger.debug("Adding docker image on the remote")
    blocking_command(ssh, f"docker load -i {image_path}")


def copy_file_to_remote(ssh: SSHClient, path: str, destination_path: str = REMOTE_DIR):
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
    profile_path = "~/.profile"
    stdout = blocking_command(
        ssh,
        f"cat {profile_path}",
    )

    if not "alias docker-compose" in stdout:
        logger.debug("Adding alias to .profile")
        alias_command = f"alias docker-compose='docker run --platform linux/arm/v7 --rm -t --privileged -v \\$(pwd):/compose -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker {DOCKER_COMPOSE_IMAGE_NAME}'"
        blocking_command(
            ssh,
            f'echo "{alias_command}" >> {profile_path}',
        )


def build_and_push_docker_compose():

    build_for_arch(
        DOCKER_COMPOSE_IMAGE_NAME,
        os.path.join(os.getcwd(), "plc-docker-compose.Dockerfile"),
    )
    with tempfile.TemporaryDirectory() as tmpdirname:
        docker_compose_local_image_path = save_docker_image(
            tmpdirname, DOCKER_COMPOSE_IMAGE_NAME, "docker-compose.tar"
        )

        with ssh_client() as ssh:
            remote_image_path = copy_file_to_remote(
                ssh, docker_compose_local_image_path
            )
            add_docker_image_on_remote(ssh, remote_image_path)
            remove_file_on_remote(  # could be disabled if enough space
                ssh, remote_image_path
            )
            add_compose_alias_to_profile(  # not necessary for the script, handy for manual use.
                ssh
            )


def build_and_push_vernemq():
    vernemq_image_name = "vernemq:latest-armv7"
    with cwd("vernemq"):
        build_for_arch(
            vernemq_image_name,
            os.path.join(os.getcwd(), "vernemq.Dockerfile"),
            no_cache=False,
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            docker_local_image_path = save_docker_image(
                tmpdirname, vernemq_image_name, "vernemq.tar"
            )

            with ssh_client() as ssh:
                remote_image_path = copy_file_to_remote(ssh, docker_local_image_path)
                add_docker_image_on_remote(ssh, remote_image_path)
                remove_file_on_remote(  # could be disabled if enough space
                    ssh, remote_image_path
                )


def build_and_push_control_app():
    control_app_image_name = "python-control-app:latest-armv7"

    with cwd("../"):
        build_for_arch(
            control_app_image_name,
            os.path.join(os.getcwd(), "python_control.Dockerfile"),
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            docker_local_image_path = save_docker_image(
                tmpdirname, control_app_image_name, "python-control-app.tar"
            )

            with ssh_client() as ssh:
                remote_image_path = copy_file_to_remote(ssh, docker_local_image_path)
                add_docker_image_on_remote(ssh, remote_image_path)
                remove_file_on_remote(  # could be disabled if enough space
                    ssh, remote_image_path
                )


def copy_docker_compose_files_to_plc():
    logger.debug("Starting with copying docker compose file to plc")

    local_file_path = "plc.docker-compose.yml"
    remote_file_path = os.path.join(REMOTE_DOCKER_COMPOSE_DIR, "docker-compose.yml")

    with ssh_client() as ssh:
        logger.debug(f"Creating directory {os.path.dirname(remote_file_path)}")
        blocking_command(ssh, f"mkdir {REMOTE_DOCKER_COMPOSE_DIR}")
        copy_file_to_remote(ssh, local_file_path, remote_file_path)
        local_cert_path = "vernemq/bridge/certificate/ISRG_ROOT_X1.crt"
        copy_file_to_remote(
            ssh,
            os.path.join(os.getcwd(), local_cert_path),
            REMOTE_DOCKER_COMPOSE_DIR,
        )


def create_env_file():
    with ssh_client() as ssh:
        envs = [
            (MQTT_PASSWORD_ENV_NAME, os.getenv(MQTT_PASSWORD_ENV_NAME)),
            (CLOUD_VERNEMQ_ENV_NAME, os.getenv(CLOUD_VERNEMQ_ENV_NAME)),
            (PAGERDUTY_KEY_ENV_NAME, os.getenv(PAGERDUTY_KEY_ENV_NAME)),
            ("CERTIFICATE_DIR", REMOTE_DOCKER_COMPOSE_DIR),
            ("MQTT_HOST", "vernemq"),
            ("SEND_NOTIFICATIONS", True),
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
        docker_compose_alias = f"docker run --rm -t --privileged -v $(pwd):/compose -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker {DOCKER_COMPOSE_IMAGE_NAME}"
        compose_command = (
            f"cd {REMOTE_DOCKER_COMPOSE_DIR} && {docker_compose_alias} up -d control"
        )
        logger.debug(f"Running '{compose_command}'")
        blocking_command(ssh, compose_command)
        logger.debug("Done running compose command")


if __name__ == "__main__":
    start = time.time()
    build_and_push_docker_compose()
    build_and_push_vernemq()
    build_and_push_control_app()
    copy_docker_compose_files_to_plc()
    create_env_file()
    run_docker_compose()
    stop = time.time()
    logger.debug(f"Script took {stop - start} seconds.")
