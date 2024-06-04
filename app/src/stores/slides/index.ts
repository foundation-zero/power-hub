import type { PresentationItem } from "@/types";
import electrical from "./electrical";
import thermal from "./thermal";
import water from "./water";
import {
  activateAllComponents,
  deactivateAll,
  showAll,
  sleep,
  toggleWaves,
  toggleWidgets,
} from "./actions";

const items: PresentationItem[] = [
  toggleWidgets(true),
  activateAllComponents,
  sleep(5000),
  ...electrical,
  [0],
  showAll,
  toggleWaves(true),
  toggleWidgets(true),
  ...thermal,
  [0],
  showAll,
  toggleWaves(true),
  toggleWidgets(true),
  ...water,
  [0],
  showAll,
  toggleWaves(true),
  toggleWidgets(true),
  deactivateAll("electrical"),
];

export default items;
