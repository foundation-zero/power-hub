import Base from "@/components/slides/water/BaseWater.vue";
import RecycleTriangle from "@/components/slides/water/RecycleTriangle.vue";
import ThreeTimes from "@/components/slides/water/ThreeTimes.vue";
import SavedDots from "@/components/slides/water/SavedDots.vue";
import WaterHowDoesItWork from "@/components/slides/water/HowDoesItWork.vue";
import ReusingWater from "@/components/slides/water/ReusingWater.vue";
import SavedEnergy from "@/components/slides/water/SavedEnergy.vue";
import WeCanReuseIt from "@/components/slides/water/WeCanReuseIt.vue";
import ByReusingIt from "@/components/slides/water/ByReusingIt.vue";
import GreyWaterIsUsed from "@/components/slides/water/GreyWaterIsUsed.vue";
import type { PresentationItem } from "@/types";
import {
  activateStream,
  deactivateAll,
  hideAll,
  sleep,
  toggleWaves,
  toggleWidgets,
} from "./actions";
import { startFlow } from "@/utils";

export default [
  ({ setJourney }) => setJourney("water"),
  deactivateAll("water"),
  activateStream("water"),
  ({ getFlow }) => getFlow("water").streams.forEach(startFlow),
  sleep(5000),
  toggleWidgets(false),
  hideAll("water"),
  toggleWaves(false),
  [1000, Base],
  [500, RecycleTriangle, Base],
  [500, RecycleTriangle, Base, ThreeTimes],
  [1000, RecycleTriangle, Base, ThreeTimes, SavedDots],
  [5000, RecycleTriangle, Base, ThreeTimes, SavedDots, WaterHowDoesItWork],
  [5000, RecycleTriangle, Base, ThreeTimes, SavedEnergy, ReusingWater],
  [5000, RecycleTriangle, Base, ThreeTimes, SavedEnergy, WeCanReuseIt, ByReusingIt],
  [7000, RecycleTriangle, Base, ThreeTimes, SavedEnergy, GreyWaterIsUsed, ByReusingIt],
] as PresentationItem[];
