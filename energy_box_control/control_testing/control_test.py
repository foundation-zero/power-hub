import argparse
import dataclasses
import time
import json
from energy_box_control.custom_logging import get_logger
from energy_box_control.monitoring.monitoring import Notifier
from energy_box_control.mqtt import create_and_connect_client, publish_to_mqtt
from energy_box_control.network import NetworkControl
from energy_box_control.power_hub.control.control import (
    control_from_json,
    control_to_json,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules

logger = get_logger(__name__)


CONTROL_VALUES_TOPIC = "power_hub/control_values"


class ControlTester:

    def __init__(self, seconds: int) -> None:
        self._power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
        self._mqtt_client = create_and_connect_client()
        with open("energy_box_control/control_testing/control_all_off.json") as f:
            self.everything_off_control: NetworkControl[PowerHub] = control_from_json(
                self._power_hub,
                json.dumps(json.load(f)),
            )
        self._seconds = seconds

    def publish(self, control: NetworkControl[PowerHub]):
        publish_to_mqtt(
            self._mqtt_client,
            CONTROL_VALUES_TOPIC,
            control_to_json(self._power_hub, control),
            Notifier(),
        )

    def everything_off(self):
        logger.info("Turning all controls off")
        self.publish(self.everything_off_control)

    def modified_control(
        self, app_name: str, control_name: str, control_value: bool | float
    ):
        new_control = self.everything_off_control.replace_control(
            getattr(self._power_hub, app_name), control_name, control_value
        )
        return new_control

    def change_valve_position(self, valve_name: str, position: float):
        logger.info(f"Turning {valve_name} to {position}")
        new_control = self.modified_control(valve_name, "position", position)
        self.publish(new_control)

    def turn_on(self, pump_name: str):
        logger.info(f"Turning {pump_name} on")
        new_control = self.modified_control(pump_name, "on", True)
        self.publish(new_control)

    def test_valves(self):
        self.everything_off()
        for valve_name in [
            field.name
            for field in dataclasses.fields(self._power_hub)
            if "valve" in field.name
        ]:
            self.change_valve_position(valve_name, 1.0)
            time.sleep(self._seconds)

    def test_pumps(self):
        self.everything_off()
        for pump_name in [
            field.name
            for field in dataclasses.fields(self._power_hub)
            if "pump" in field.name
        ]:
            self.turn_on(pump_name)
            time.sleep(self._seconds)

    def test_coolers(self):
        self.everything_off()
        for app in [
            field.name
            for field in dataclasses.fields(self._power_hub)
            if field.name in ["yazaki", "chiller"]
        ]:
            self.turn_on(app)
            time.sleep(self._seconds)

    def test_custom_file(self, file_path: str):
        self.publish(
            control_from_json(self._power_hub, json.dumps(json.load(open(file_path))))
        )

    def test_all(self):
        self.everything_off()
        for app_name in [field.name for field in dataclasses.fields(self._power_hub)]:
            if "pump" in app_name or app_name in ["yazaki", "chiller"]:
                self.turn_on(app_name)
            elif "valve" in app_name:
                self.change_valve_position(app_name, 1.0)
            time.sleep(self._seconds)

    def test_single(self, app_name: str, control_name: str, value: bool | float):
        self.everything_off()
        logger.info(f"Changing {control_name} for {app_name} to {value}")
        new_control = self.modified_control(app_name, control_name, value)
        self.publish(new_control)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Control Tester", description="Test control values"
    )
    parser.add_argument(
        "-s",
        "--seconds",
        help="How many seconds to sleep between control switches.",
        default=30,
        type=int,
    )
    parser.add_argument("-f", "--filepath")
    parser.add_argument(
        "-t",
        "--test",
        choices="[test_valves, test_pumps, test_coolers, test_all, test_custom_json, test_single]",
    )
    parser.add_argument(
        "-a",
        "--appliance",
        help="Specify which appliance you want to change the control of, can only be used in combination with test_single",
    )
    parser.add_argument(
        "-c",
        "--control",
        help="Specify which control you want to change, can only be used in combination with test_single",
    )
    parser.add_argument(
        "-v",
        "--control_value",
        help="Specify which control value you want to set, can only be used in combination with test_single",
    )
    args = parser.parse_args()
    tester = ControlTester(args.seconds)
    if args.test == "test_valves":
        tester.test_valves()
    elif args.test == "test_pumps":
        tester.test_pumps()
    elif args.test == "test_coolers":
        tester.test_coolers()
    elif args.test == "test_custom_json":
        if not args.filepath:
            parser.error("--filepath is required when --test is 'test_custom_json'")
        tester.test_custom_file(args.filepath)
    elif args.test == "test_all":
        tester.test_all()
    elif args.test == "test_single":
        if not args.appliance or not args.control or not args.control_value:
            parser.error(
                "--appliance, --control and --control_value are required when --test is 'test_single'"
            )
        tester.test_single(args.appliance, args.control, args.control_value)
