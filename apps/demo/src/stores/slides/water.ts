import Base from "@demo/components/display/slides/water/BaseWater.vue";
import RecycleTriangle from "@demo/components/display/slides/water/RecycleTriangle.vue";
import ThreeTimes from "@demo/components/display/slides/water/ThreeTimes.vue";
import SavedDots from "@demo/components/display/slides/water/SavedDots.vue";
import WaterHowDoesItWork from "@demo/components/display/slides/water/HowDoesItWork.vue";
import ReusingWater from "@demo/components/display/slides/water/ReusingWater.vue";
import SavedEnergy from "@demo/components/display/slides/water/SavedEnergy.vue";
import WeCanReuseIt from "@demo/components/display/slides/water/WeCanReuseIt.vue";
import ByReusingIt from "@demo/components/display/slides/water/ByReusingIt.vue";
import GreyWaterIsUsed from "@demo/components/display/slides/water/GreyWaterIsUsed.vue";
import StepByStep from "@demo/components/display/slides/StepByStep.vue";
import ThisIs from "@demo/components/display/slides/water/ThisIs.vue";
import ThemeIcon from "@demo/components/display/slides/water/ThemeIcon.vue";
import WeUseThisTo from "@demo/components/display/slides/WeUseThisTo.vue";
import ThisProvides from "@demo/components/display/slides/water/ThisProvides.vue";
import type { PresentationItem } from "@demo/types";
import { activateStream, deactivateAll, hideAll, toggleWaves, toggleWidgets } from "./actions";
import { startFlow } from "@demo/utils";

export default [
  ({ setJourney }) => setJourney("water"),
  deactivateAll("water"),
  [0, ThemeIcon, ThisIs, WeUseThisTo],
  activateStream("water"),
  ({ getFlow }) => getFlow("water").streams.forEach(startFlow),
  [5000, ThemeIcon, StepByStep, ThisProvides],
  [0],
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
