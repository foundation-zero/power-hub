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
  };

export type PCM = Port<"charge"> &
  Port<"discharge"> & {
    temperature: number;
    stateOfCharge: number;
  };

export type Chiller = Port<"cooling"> & Port<"chilled">;

export type HeatPipes = Port & {
  ambientTemperature: number;
  globalIrradiance: number;
};

export type Reservoir = Port<"heat"> &
  Port<"fill"> & {
    temperature: number;
  };

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
}

export interface ComputedTree {
  heatPipes: {
    power: number;
  };
}

export interface Tree {
  applianceSensors: SensorsTree;
}
