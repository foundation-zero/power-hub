import Base from "@/components/display/slides/electrical/BaseElectrical.vue";
import LightBulb from "@/components/display/slides/electrical/LightBulb.vue";
import HowDoesItWork from "@/components/display/slides/electrical/HowDoesItWork.vue";
import WeProduce from "@/components/display/slides/electrical/WeProduce.vue";
import HundredPercent from "@/components/display/slides/electrical/HundredPercent.vue";
import SolarPowered from "@/components/display/slides/electrical/SolarPowered.vue";
import ThatsEquivalentTo from "@/components/display/slides/electrical/ThatsEquivalentTo.vue";
import ElectricDemand from "@/components/display/slides/electrical/ElectricDemand.vue";
import StepByStep from "@/components/display/slides/StepByStep.vue";
import ThemeIcon from "@/components/display/slides/electrical/ThemeIcon.vue";
import ThisIs from "@/components/display/slides/electrical/ThisIs.vue";
import StoredInBattery from "@/components/display/slides/electrical/StoredInBattery.vue";
import WeUseThisTo from "@/components/display/slides/WeUseThisTo.vue";
import ThisProvides from "@/components/display/slides/electrical/ThisProvides.vue";
import type { PresentationItem } from "@/types";
import { activateStream, deactivateAll, hideAll, toggleWaves, toggleWidgets } from "./actions";

export default [
  ({ setJourney }) => setJourney("electrical"),
  deactivateAll("electrical"),
  [0, ThemeIcon, ThisIs, WeUseThisTo],
  activateStream("electrical"),
  [5000, ThemeIcon, StepByStep, ThisProvides],
  [0],
  toggleWidgets(false),
  hideAll("electrical"),
  toggleWaves(false),
  [2000, Base, ElectricDemand],
  [5000, Base, ElectricDemand, LightBulb, HowDoesItWork],
  [3000, Base, ElectricDemand, LightBulb, WeProduce],
  [750, Base, ElectricDemand, LightBulb, WeProduce, HundredPercent],
  [4000, Base, ElectricDemand, LightBulb, WeProduce, HundredPercent, SolarPowered],
  [5000, Base, ElectricDemand, LightBulb, StoredInBattery, HundredPercent, SolarPowered],
  [5000, Base, ElectricDemand, LightBulb, ThatsEquivalentTo, HundredPercent, SolarPowered],
] as PresentationItem[];
