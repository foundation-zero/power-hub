import Base from "@/components/slides/electrical/BaseElectrical.vue";
import HowDoesItWork from "@/components/slides/electrical/HowDoesItWork.vue";
import WeProduce from "@/components/slides/electrical/WeProduce.vue";
import HundredPercent from "@/components/slides/electrical/HundredPercent.vue";
import SolarPowered from "@/components/slides/electrical/SolarPowered.vue";
import ThatsEquivalentTo from "@/components/slides/electrical/ThatsEquivalentTo.vue";

export default [
  [2000, Base],
  [5000, Base, HowDoesItWork],
  [3000, Base, WeProduce],
  [2000, Base, WeProduce, HundredPercent],
  [4000, Base, WeProduce, HundredPercent, SolarPowered],
  [7000, Base, ThatsEquivalentTo, HundredPercent, SolarPowered],
] as [duration: number, ...slides: (typeof Base)[]][];
