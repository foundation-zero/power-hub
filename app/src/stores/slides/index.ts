import type { PresentationItem } from "@/types";
import electrical from "./electrical";
import thermal from "./thermal";
import water from "./water";
import {
  activateAllComponents,
  deactivateAll,
  resetAll,
  showAll,
  sleep,
  toggleWaves,
  toggleWidgets,
} from "./actions";
import { hide } from "@/utils";

const items: PresentationItem[] = [
  ({ streamStates }) => streamStates.forEach(hide),
  // toggleWidgets(true),
  // activateAllComponents,
  // sleep(5000),
  // ...electrical,
  // [0],
  // showAll,
  // toggleWaves(true),
  // toggleWidgets(true),
  ...thermal,
  resetAll,
  [0],
  showAll,
  toggleWaves(true),
  toggleWidgets(true),
  ...water,
  resetAll,
  [0],
  showAll,
  toggleWaves(true),
  toggleWidgets(true),
  resetAll,
  deactivateAll("electrical"),
];

export default items;
