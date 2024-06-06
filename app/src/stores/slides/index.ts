import type { PresentationItem } from "@/types";
import electrical from "./electrical";
import thermal from "./thermal";
import water from "./water";
import {
  activateAllComponents,
  deactivateAll,
  resetAll,
  showAll,
  toggleWaves,
  toggleWidgets,
} from "./actions";
import { hide } from "@/utils";
import WelcomeToThePowerHub from "@/components/map/WelcomeToThePowerHub.vue";

const items: PresentationItem[] = [
  ({ streamStates }) => streamStates.forEach(hide),
  toggleWidgets(true),
  activateAllComponents,
  [0, WelcomeToThePowerHub],
  ...electrical,
  [0],
  showAll,
  toggleWaves(true),
  toggleWidgets(true),
  ...thermal,
  resetAll,
  [0, WelcomeToThePowerHub],
  showAll,
  toggleWaves(true),
  toggleWidgets(true),
  ...water,
  resetAll,
  [0, WelcomeToThePowerHub],
  showAll,
  toggleWaves(true),
  toggleWidgets(true),
  resetAll,
  deactivateAll("electrical"),
];

export default items;
