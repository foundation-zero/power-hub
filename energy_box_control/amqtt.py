from logging import Logger

import aiomqtt
from aiomqtt import TLSParameters

from energy_box_control.config import CONFIG


def get_mqtt_client(logger: Logger):
    if CONFIG.mqtt_tls_enabled:
        tls_parameters = TLSParameters(ca_certs=CONFIG.mqtt_tls_path)
    else:
        tls_parameters = None

    return aiomqtt.Client(
        "localhost",
        port=CONFIG.mqtt_port,
        username=CONFIG.mqtt_username,
        password=CONFIG.mqtt_password,
        logger=logger,
        tls_params=tls_parameters,
    )
