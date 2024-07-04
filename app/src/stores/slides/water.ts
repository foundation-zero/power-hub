import Base from "@/components/display/slides/water/BaseWater.vue";
import RecycleTriangle from "@/components/display/slides/water/RecycleTriangle.vue";
import ThreeTimes from "@/components/display/slides/water/ThreeTimes.vue";
import SavedDots from "@/components/display/slides/water/SavedDots.vue";
import WaterHowDoesItWork from "@/components/display/slides/water/HowDoesItWork.vue";
import ReusingWater from "@/components/display/slides/water/ReusingWater.vue";
import SavedEnergy from "@/components/display/slides/water/SavedEnergy.vue";
import WeCanReuseIt from "@/components/display/slides/water/WeCanReuseIt.vue";
import ByReusingIt from "@/components/display/slides/water/ByReusingIt.vue";
import GreyWaterIsUsed from "@/components/display/slides/water/GreyWaterIsUsed.vue";
import StepByStep from "@/components/display/slides/StepByStep.vue";
import ThisIs from "@/components/display/slides/water/ThisIs.vue";
import ThemeIcon from "@/components/display/slides/water/ThemeIcon.vue";
import WeUseThisTo from "@/components/display/slides/WeUseThisTo.vue";
import ThisProvides from "@/components/display/slides/water/ThisProvides.vue";
import type { PresentationItem } from "@/types";
import { activateStream, deactivateAll, hideAll, toggleWaves, toggleWidgets } from "./actions";
import { startFlow } from "@/utils";

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
