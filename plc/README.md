# Prerequisites:

## Setup SSH proxy jump and add right configs

## Install or enable Docker on the remote machine (is pre-installed on PLCs with firmware versions above 20).

## Add user to the docker group: 

`sudo usermod -aG docker $USER`

## Enable experimental features for Docker

On your local machine (Docker Desktop -> Preferences -> Docker Engine) to be able to build the docker-compose image for the right platform.

## OPTIONAL: This shouldn't happen, but if you encounter: 
`exec /usr/bin/docker-compose: exec format error`

You might need to enable qemu by running:

`docker run --rm --privileged multiarch/qemu-user-static --reset -p yes`

## Make sure that all variables are correct. 

## Test
To test whether the script ran succesful you can docker exec into the control-app container and run:

`/app/env/bin/python -m energy_box_control.plc_tests.test_mqtt`

Which should put a sensor_values json on MQTT (if the bridge is enabled it will propagate to Telegraf and InfluxDB) and trigger an alert to PagerDuty. Try to clean up after. 

## Run configure_plc.py

To automatically configure the docker on the PLC run:

```bash
poetry run python plc/configure_plc.py
```