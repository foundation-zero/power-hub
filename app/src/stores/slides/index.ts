import type { PresentationItem } from "@/types";
import electrical from "./electrical";
import thermal from "./thermal";
import water from "./water";
import { activateAllComponents, resetAll, showAll, toggleWaves, toggleWidgets } from "./actions";
import { hide } from "@/utils";
import WelcomeToThePowerHub from "@/components/slides/WelcomeToThePowerHub.vue";

const journeyFn = (items: PresentationItem[]): PresentationItem[] => [
  toggleWaves(true),
  toggleWidgets(true),
  activateAllComponents,
  [0, WelcomeToThePowerHub],
  ...items,
  [750],
  resetAll,
  showAll,
];

const items: PresentationItem[] = [
  ({ streamStates }) => streamStates.forEach(hide),
  ...journeyFn(electrical),
  ...journeyFn(thermal),
  ...journeyFn(water),
];

export default items;
