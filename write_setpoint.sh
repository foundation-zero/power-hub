#!/bin/sh
poetry run python -m energy_box_control.plc_tests.write_setpoint "$@"
