import type { CamelCase } from "type-fest";

type Port<PortName extends string = ""> = {
  [key in CamelCase<`${PortName}${"DeltaTemperature" | "InputTemperature" | "OutputTemperature" | "Flow" | "Power"}`>]: number;
};

export interface Valve {
  position: number;
}

export interface Pump extends Appliance {
  setpoint: number;
}

export interface Appliance {
  on: boolean;
}

export type Yazaki = Port<"hot"> &
  Port<"cooling"> &
  Port<"chilled"> & {
    efficiency: number;
    wastePower: number;
    chillPower: number;
    usedPower: number;
    operationOutput: boolean;
  };

export type PCM = Port<"charge"> &
  Port<"discharge"> & {
    temperature: number;
    stateOfCharge: number;
    chargePower: number;
    dischargePower: number;
    netCharge: number;
    heat: number;
  };

export type Chiller = Port<"cooling"> &
  Port<"chilled"> & {
    chillPower: number;
    status: boolean;
    wasteHeat: number;
  };

export type HeatPipes = Port & {
  ambientTemperature: number;
  globalIrradiance: number;
  power: number;
};

export type Reservoir = Port<"heat"> &
  Port<"fill"> & {
    temperature: number;
    coolingSupply: number;
  };

export type PVPanel = {
  power: number;
};

export interface WaterTank {
  fill: number;
  fillRatio: number;
  waterTreatmentFlowIn: number;
  waterMakerFlowIn: number;
  waterDemandFlow: number;
}

export interface WaterMaker {
  productionFlow: number;
  currentProduction: number;
  status: 0 | 1 | 2 | 3;
}

export interface WaterTreatment {
  outFlow: number;
}

export interface Weather {
  globalIrradiance: number;
  ambientTemperature: number;
}

export interface Compound {
  overallTemperature: number;
}

export interface Electrical {
  batterySystemSoc: number;
  pvPower: number;
  powerConsumption: number;
  compoundPowerConsumption: number;
  vebusChargeState: 0 | 1 | 2;
  gridPower: number;
  totalAcPower: number;
  batterySystemPower: number;
}

export interface Fancoil {
  ambientTemperature: number;
  mode: number;
  fanSpeedMode: number;
  operatingModeWaterTemperature: number;
  batteryWaterTemperature: number;
  setpoint: number;
}

export interface FlowPort {
  hotTemperature: number;
  hotTemperatureStatus: 0 | 1;
  coldTemperature: number;
  coldTemperatureStatus: 0 | 1;
  deltaTemperature: number;
  deltaTemperatureStatus: 0 | 1;
}

export interface FlowSensor {
  flow: number;
  glycol_concentration: number;
  total_volume: number;
  temperature: number;
  status: number;
}

export interface SensorsTree {
  heatPipes: HeatPipes;
  heatPipesValve: Valve;
  hotReservoirPCMValve: Valve;
  hotReservoir: Reservoir;
  pcm: PCM;
  yazakiHotBypassValve: Valve;
  yazaki: Yazaki;
  chiller: Chiller;
  chillerSwitchValve: Valve;
  coldReservoir: Reservoir & { coolingDemand: number };
  yazakiWasteBypassValve: Valve;
  preheatBypassValve: Valve;
  preheatReservoir: Reservoir;
  wasteSwitchValve: Valve;
  hotReservoirPcmValve: Valve;
  chillerWasteBypassValve: Valve;
  pvPanel: PVPanel;
  waterTreatment: WaterTreatment;
  waterMaker: WaterMaker;
  weather: Weather;
  compound: Compound;
  electrical: Electrical;

  powerHubFancoil: Fancoil;
  office1Fancoil: Fancoil;
  office2Fancoil: Fancoil;
  sanitaryFancoil: Fancoil;
  kitchenFancoil: Fancoil;
  simulatorFancoil: Fancoil;
  rh33PcmDischarge: FlowPort;
  rh33Preheat: FlowPort;
  rh33DomesticHotWater: FlowPort;
  rh33HeatPipes: FlowPort;
  rh33HotStorage: FlowPort;
  rh33YazakiHot: FlowPort;
  rh33Waste: FlowPort;
  rh33Chill: FlowPort;
  rh33HeatDdump: FlowPort;
  rh33CoolingDemand: FlowPort;
  outboardExchange: Port;

  freshWaterTank: WaterTank & { flowToTechnical: number; flowToKitchen: number };
  greyWaterTank: WaterTank;
  blackWaterTank: WaterTank;
  technicalWaterTank: WaterTank;
  outboardTemperatureSensor: {
    temperature: number;
  };

  yazakiHotFlowSensor: FlowSensor;
  wasteFlowSensor: FlowSensor;
  chilledFlowSensor: FlowSensor;
  coolingDemandFlowSensor: FlowSensor;
}

export type Watt = number;
export type Joule = number;

export interface ElectricPower {
  consumption: Watt;
  production: Watt;
}

export interface Electric {
  power: ElectricPower;
}

export interface SumTree {
  electric: Electric;
}

export interface Tree {
  sensorValues: SensorsTree;
  powerHub: SumTree;
  controlValues: ControlValues;
}

export type PowerHubComponent =
  | "sun"
  | "solar-panels"
  | "heat-tubes"
  | "heat-storage"
  | "absorption-chiller"
  | "compression-chiller"
  | "cooling-demand"
  | "power-battery"
  | "system-demand"
  | "sea-water"
  | "water-maker"
  | "water-storage"
  | "water-treatment"
  | "water-demand";

export type DateRange = [from: string, to: string];

export type TimeInterval = "d" | "h" | "min" | "s";

export interface ControlValues {
  coolingDemandPump: Pump;
  hotSwitchValve: Valve;
  heatPipesValve: Valve;
  heatPipesSupplyBoxPump: Pump;
  heatPipesPowerHubPump: Pump;
  wasteBypass: Valve;
  yazakiHotBypass: Valve;
  wasteSwitch: Valve;
  chillerSwitch: Valve;
  chiller: Appliance;
  yazaki: Appliance;
  chilledLoopPump: Pump;
  pcmToYazakiPump: Pump;
  wastePump: Pump;
  outboardPump: Appliance & {
    frequencyRatio: number;
  };
  waterFilterBypassValve: Valve;
  technicalWaterRegulator: Valve;
  waterTreatment: Appliance;
  time: number;
}
