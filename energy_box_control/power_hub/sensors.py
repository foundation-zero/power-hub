from dataclasses import dataclass
from energy_box_control.appliances import HeatPipes, HeatPipesPort
from energy_box_control.appliances.heat_exchanger import (
    HeatExchanger,
    HeatExchangerPort,
)
from energy_box_control.appliances.mix import Mix, MixPort
from energy_box_control.units import (
    Celsius,
    JoulePerLiterKelvin,
    LiterPerSecond,
    Watt,
    WattPerMeterSquared,
)
from energy_box_control.appliances.boiler import Boiler, BoilerPort
from energy_box_control.appliances.chiller import Chiller, ChillerPort
from energy_box_control.appliances.pcm import Pcm, PcmPort
from energy_box_control.appliances.valve import Valve, ValvePort
from energy_box_control.appliances.yazaki import Yazaki, YazakiPort
from energy_box_control.sensors import (
    FromState,
    SensorType,
    sensor,
    sensors,
    NetworkSensors,
)


@sensors()
class HeatPipesSensors(FromState):
    spec: HeatPipes
    flow: LiterPerSecond = sensor(
        technical_name="FS1001", type=SensorType.FLOW, from_port=HeatPipesPort.IN
    )
    ambient_temperature: Celsius = sensor(from_weather=True)
    global_irradiance: WattPerMeterSquared = sensor(from_weather=True)
    input_temperature: Celsius = sensor(
        technical_name="TS1001", type=SensorType.TEMPERATURE, from_port=HeatPipesPort.IN
    )
    output_temperature: Celsius = sensor(
        technical_name="TS1002",
        type=SensorType.TEMPERATURE,
        from_port=HeatPipesPort.OUT,
    )

    @property
    def power(self) -> Watt:
        return (
            self.flow
            * (self.output_temperature - self.input_temperature)
            * self.spec.specific_heat_medium
        )


@sensors()
class PcmSensors(FromState):
    spec: Pcm
    yazaki: "YazakiSensors"
    heat_pipes: "HeatPipesSensors"
    hot_reservoir_pcm_valve: "ValveSensors"  # CV1001
    temperature: Celsius = sensor(technical_name="TS1007")

    charge_input_temperature: Celsius = sensor(
        technical_name="TS1005",
        type=SensorType.TEMPERATURE,
        from_port=PcmPort.CHARGE_IN,
    )
    charge_output_temperature: Celsius = sensor(
        technical_name="TS1006",
        type=SensorType.TEMPERATURE,
        from_port=PcmPort.CHARGE_OUT,
    )

    discharge_flow: LiterPerSecond = sensor(
        technical_name="FS1003", type=SensorType.FLOW, from_port=PcmPort.DISCHARGE_IN
    )

    @property
    def discharge_input_temperature(self) -> Celsius:
        return self.yazaki.hot_output_temperature

    @property
    def discharge_power(
        self,
    ) -> (
        Watt
    ):  # this is problematic if we want to know losses / energy that goes into heating up circuit. Unless we can infer from the position of the bypass valve
        return self.yazaki.used_heat

    @property
    def discharge_output_temperature(
        self,
    ) -> Celsius:  # base this on pcm internal temp?
        return (
            self.discharge_power
            / (self.spec.specific_heat_capacity_discharge * self.discharge_flow)
        ) + self.discharge_input_temperature

    @property
    def charge_power(
        self,
    ) -> Watt:  # this is problematic if we want to know losses in the system
        return (
            self.heat_pipes.power if self.hot_reservoir_pcm_valve.position == 0 else 0
        )

    @property
    def charge_flow(self) -> LiterPerSecond:
        return self.charge_power / (
            self.spec.specific_heat_capacity_charge
            * (self.charge_input_temperature - self.charge_output_temperature)
        )

    @property
    def net_charge(self) -> Watt:
        return self.charge_power - self.discharge_power

    @property
    def charged(self) -> bool:
        return self.temperature > self.spec.phase_change_temperature

    @property
    def state_of_charge(self):
        return float(self.temperature > self.spec.phase_change_temperature)


@sensors()
class YazakiSensors(FromState):
    spec: Yazaki
    chiller_switch_valve: "ValveSensors"
    chill_mix: "MixSensors"  # replace by cold reservoir?
    outboard_exchange: "HeatExchangerSensors"
    # preheat_reservoir: "PreheatReservoirSensors"
    hot_flow: LiterPerSecond = sensor(
        technical_name="FS1004", type=SensorType.FLOW, from_port=YazakiPort.HOT_IN
    )
    hot_input_temperature: Celsius = sensor(
        technical_name="TS1010",
        type=SensorType.TEMPERATURE,
        from_port=YazakiPort.HOT_IN,
    )
    hot_output_temperature: Celsius = sensor(
        technical_name="TS1011",
        type=SensorType.TEMPERATURE,
        from_port=YazakiPort.HOT_OUT,
    )

    cooling_flow: LiterPerSecond = (
        sensor(  # Would need to resolve using preheat and waste exchange power
            type=SensorType.FLOW, from_port=YazakiPort.COOLING_IN
        )
    )

    cooling_input_temperature: Celsius = sensor(
        technical_name="TS1014",
        type=SensorType.TEMPERATURE,
        from_port=YazakiPort.COOLING_IN,
    )
    cooling_output_temperature: Celsius = sensor(
        technical_name="TS1015",
        type=SensorType.TEMPERATURE,
        from_port=YazakiPort.COOLING_OUT,
    )

    @property
    def chilled_input_temperature(self) -> Celsius:  # TS1023
        return (
            self.chiller_switch_valve.input_temperature
            if self.chiller_switch_valve.position == 0
            else float("nan")
        )

    @property
    def chilled_output_temperature(
        self,
    ) -> (
        Celsius
    ):  # TS1024  #instead of on the mix, can define it on the cold_reservoir_in..
        return (
            self.chill_mix.output_temperature
            if self.chiller_switch_valve.position == 0
            else float("nan")
        )

    @property
    def chilled_flow(
        self,
    ) -> (
        LiterPerSecond
    ):  # FS1006   #instead of on the mix, can define it on the cold_reservoir_in..
        return (
            self.chill_mix.output_flow
            if self.chiller_switch_valve.position == 0
            else float("nan")
        )

    @property
    def cool_power(self) -> Watt:
        return (
            self.chilled_flow
            * (self.chilled_input_temperature - self.chilled_output_temperature)
            * self.spec.specific_heat_capacity_chilled
        )

    @property
    def waste_heat(self) -> Watt:
        # return self.cooling_flow * (self.cooling_output_temperature - self.cooling_input_temperature) * self.spec.specific_heat_capacity_cooling
        return (
            (self.outboard_exchange.power)
            if self.chiller_switch_valve.position == 0
            else float("nan")
        )  # add preheat reservoir power

    @property
    def used_heat(self) -> Watt:
        return (
            self.hot_flow
            * (self.hot_input_temperature - self.hot_output_temperature)
            * self.spec.specific_heat_capacity_hot
        )

    @property
    def efficiency(self) -> float:
        return self.used_heat / self.cool_power if self.cool_power > 0 else float("nan")


@sensors()
class HeatExchangerSensors(FromState):
    spec: HeatExchanger
    input_temperature: Celsius = sensor(
        technical_name="TS1035",
        type=SensorType.TEMPERATURE,
        from_port=HeatExchangerPort.A_IN,
    )
    output_temperature: Celsius = sensor(
        technical_name="TS1036",
        type=SensorType.TEMPERATURE,
        from_port=HeatExchangerPort.A_OUT,
    )
    flow: LiterPerSecond = sensor(
        technical_name="FS1009", type=SensorType.FLOW, from_port=HeatExchangerPort.A_OUT
    )

    @property
    def power(self) -> Watt:
        return (
            self.flow
            * (self.output_temperature - self.input_temperature)
            * self.spec.specific_heat_capacity_A
        )


@sensors()
class BoilerSensors(FromState):
    spec: Boiler
    temperature: Celsius
    heat_exchange_in_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.HEAT_EXCHANGE_IN
    )
    heat_exchange_out_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.HEAT_EXCHANGE_OUT
    )
    fill_in_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.FILL_IN
    )
    fill_out_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=BoilerPort.FILL_OUT
    )


@sensors()
class ValveSensors(FromState):
    spec: Valve
    position: float
    input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ValvePort.AB
    )


@sensors()
class MixSensors(FromState):
    spec: Mix
    output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=MixPort.AB
    )
    output_flow: LiterPerSecond = sensor(type=SensorType.FLOW, from_port=MixPort.AB)

    def in_position(self, position: float, diff: float = 0.05) -> bool:
        return abs(self.position - position) < diff


def derive_flow(
    power: Watt,
    valve: ValveSensors,
    temperature_in: Celsius,
    temperature_out: Celsius,
    specific_heat_capacity: JoulePerLiterKelvin,
    open_valve_state: float,
) -> LiterPerSecond:
    if not valve.position == open_valve_state:
        return 0
    return power / ((temperature_in - temperature_out) * specific_heat_capacity)


@sensors()
class HotReservoirSensors(BoilerSensors):
    fill_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=BoilerPort.FILL_IN
    )
    heat_pipes: HeatPipesSensors
    hot_reservoir_pcm_valve: ValveSensors

    @property
    def heat_exchange_flow(self) -> LiterPerSecond:
        return derive_flow(
            self.heat_pipes.power,
            self.hot_reservoir_pcm_valve,
            self.heat_exchange_in_temperature,
            self.heat_exchange_out_temperature,
            self.spec.specific_heat_capacity_exchange,
            1,
        )


@sensors()
class ChillerSensors(FromState):
    spec: Chiller
    cooling_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=ChillerPort.COOLING_IN
    )
    cooling_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.COOLING_IN
    )
    cooling_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.COOLING_OUT
    )

    chilled_flow: LiterPerSecond = sensor(
        type=SensorType.FLOW, from_port=ChillerPort.CHILLED_IN
    )
    chilled_input_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.CHILLED_IN
    )
    chilled_output_temperature: Celsius = sensor(
        type=SensorType.TEMPERATURE, from_port=ChillerPort.CHILLED_OUT
    )


@dataclass
class PowerHubSensors(NetworkSensors):
    heat_pipes: HeatPipesSensors
    heat_pipes_valve: ValveSensors
    hot_reservoir_pcm_valve: ValveSensors
    hot_reservoir: HotReservoirSensors
    pcm: PcmSensors
    yazaki_hot_bypass_valve: ValveSensors
    yazaki: YazakiSensors
    chiller: ChillerSensors
    chiller_switch_valve: ValveSensors
    cold_reservoir: BoilerSensors
    yazaki_waste_bypass_valve: ValveSensors
    preheat_bypass_valve: ValveSensors
    preheat_reservoir: BoilerSensors
    waste_switch_valve: ValveSensors
    chiller_waste_bypass_valve: ValveSensors


SensorName = str
SensorValue = float | Celsius | LiterPerSecond | WattPerMeterSquared


def get_sensor_values(
    sensor_name: SensorName, sensors: PowerHubSensors
) -> dict[SensorName, SensorValue]:
    attr = getattr(sensors, sensor_name)

    return {
        field: getattr(attr, field)
        for field in dir(attr)
        if field[0] != "_" and (type(getattr(attr, field)) in [float, int, bool])
    }
