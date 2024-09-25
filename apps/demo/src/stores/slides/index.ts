import type { PresentationItem } from "@demo/types";
import electrical from "./electrical";
import thermal from "./thermal";
import water from "./water";
import { activateAllComponents, resetAll, showAll, toggleWaves, toggleWidgets } from "./actions";
import { hide } from "@demo/utils";
import WelcomeToThePowerHub from "@demo/components/display/intro/WelcomeToThePowerHub.vue";
import ElectricEnergy from "@demo/components/display/intro/ElectricEnergy.vue";
import ThermalEnergy from "@demo/components/display/intro/ThermalEnergy.vue";
import WaterManagement from "@demo/components/display/intro/WaterManagement.vue";

const journeyFn = (items: PresentationItem[]): PresentationItem[] => [
  toggleWaves(true),
  toggleWidgets(true),
  activateAllComponents,
  ...items,
  [750],
  resetAll,
  showAll,
];

const items: PresentationItem[] = [
  ({ streamStates }) => streamStates.forEach(hide),
  [10000, WelcomeToThePowerHub],
  [10000, ElectricEnergy],
  [10000, ThermalEnergy],
  [10000, WaterManagement],
  [250],
  ...journeyFn(electrical),
  ...journeyFn(thermal),
  ...journeyFn(water),
];

export default items;
