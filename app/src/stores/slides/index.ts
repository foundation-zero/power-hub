import type { PresentationItem } from "@/types";
import electrical from "./electrical";
import thermal from "./thermal";
import water from "./water";
import { activateAllComponents, resetAll, showAll, toggleWaves, toggleWidgets } from "./actions";
import { hide } from "@/utils";
import WelcomeToThePowerHub from "@/components/display/intro/WelcomeToThePowerHub.vue";
import ElectricEnergy from "@/components/display/intro/ElectricEnergy.vue";
import ThermalEnergy from "@/components/display/intro/ThermalEnergy.vue";
import WaterManagement from "@/components/display/intro/WaterManagement.vue";

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
  [7000, WelcomeToThePowerHub],
  [7000, ElectricEnergy],
  [7000, ThermalEnergy],
  [7000, WaterManagement],
  [250],
  ...journeyFn(electrical),
  ...journeyFn(thermal),
  ...journeyFn(water),
];

export default items;
