import Base from "@/components/slides/electrical/BaseElectrical.vue";
import LightBulb from "@/components/slides/electrical/LightBulb.vue";
import HowDoesItWork from "@/components/slides/electrical/HowDoesItWork.vue";
import WeProduce from "@/components/slides/electrical/WeProduce.vue";
import HundredPercent from "@/components/slides/electrical/HundredPercent.vue";
import SolarPowered from "@/components/slides/electrical/SolarPowered.vue";
import ThatsEquivalentTo from "@/components/slides/electrical/ThatsEquivalentTo.vue";
import ElectricDemand from "@/components/slides/electrical/ElectricDemand.vue";
import type { PresentationItem } from "@/types";
import {
  activateStream,
  deactivateAll,
  hideAll,
  sleep,
  toggleWaves,
  toggleWidgets,
} from "./actions";

export default [
  ({ setJourney }) => setJourney("electrical"),
  deactivateAll("electrical"),
  activateStream("electrical"),
  sleep(3000),
  [0],
  toggleWidgets(false),
  hideAll("electrical"),
  toggleWaves(false),
  [2000, Base, ElectricDemand],
  [5000, Base, ElectricDemand, LightBulb, HowDoesItWork],
  [3000, Base, ElectricDemand, LightBulb, WeProduce],
  [750, Base, ElectricDemand, LightBulb, WeProduce, HundredPercent],
  [4000, Base, ElectricDemand, LightBulb, WeProduce, HundredPercent, SolarPowered],
  [7000, Base, ElectricDemand, LightBulb, ThatsEquivalentTo, HundredPercent, SolarPowered],
] as PresentationItem[];
