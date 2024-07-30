import type { CamelCase } from "type-fest";

type Port<PortName extends string = ""> = {
  [key in CamelCase<`${PortName}${"InputTemperature" | "OutputTemperature" | "Flow"}`>]: number;
};

export interface Valve {
  position: number;
}

export type Yazaki = Port<"hot"> &
  Port<"cooling"> &
  Port<"chilled"> & {
    efficiency: number;
    wastePower: number;
    chillPower: number;
    usedPower: number;
  };

export type PCM = Port<"charge"> &
  Port<"discharge"> & {
    temperature: number;
    stateOfCharge: number;
    chargePower: number;
    dischargePower: number;
    netCharge: number;
    fill: number;
  };

export type Chiller = Port<"cooling"> &
  Port<"chilled"> & {
    chillPower: number;
  };

export type HeatPipes = Port & {
  ambientTemperature: number;
  globalIrradiance: number;
  power: number;
};

export type Reservoir = Port<"heat"> &
  Port<"fill"> & {
    temperature: number;
    usedPower: number;
    fillPower: number;
  };

export type PVPanel = {
  power: number;
};

export interface WaterTank {
  fill: number;
  waterTreatmentFlowIn: number;
  waterMakerFlowIn: number;
  waterDemandFlow: number;
}

export interface WaterProcessor {
  outFlow: number;
}

export interface Weather {
  globalIrradience: number;
}

export interface Compound {
  overallTemperature: number;
}

export interface Electrical {
  socBatterySystem: number;
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
  coldReservoir: Reservoir;
  yazakiWasteBypassValve: Valve;
  preheatBypassValve: Valve;
  preheatReservoir: Reservoir;
  wasteSwitchValve: Valve;
  hotReservoirPcmValve: Valve;
  chillerWasteBypassValve: Valve;
  pvPanel: PVPanel;
  freshWaterTank: WaterTank;
  waterTreatment: WaterProcessor;
  waterMaker: WaterProcessor;
  weather: Weather;
  compound: Compound;
  electrical: Electrical;
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
  applianceSensors: SensorsTree;
  powerHub: SumTree;
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
