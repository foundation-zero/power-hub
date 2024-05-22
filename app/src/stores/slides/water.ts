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
import GraphicShower from "@/components/slides/water/GraphicShower.vue";
import GraphicBoatWash from "@/components/slides/water/GraphicBoatWash.vue";
import GraphicToilet from "@/components/slides/water/GraphicToilet.vue";

export default [
  [1000, Base],
  [1000, Base, RecycleTriangle],
  [1000, Base, RecycleTriangle, ThreeTimes],
  [1000, Base, RecycleTriangle, ThreeTimes, SavedDots],
  [5000, Base, RecycleTriangle, ThreeTimes, SavedDots, WaterHowDoesItWork],
  [5000, Base, RecycleTriangle, ThreeTimes, SavedEnergy, ReusingWater],
  [5000, Base, RecycleTriangle, ThreeTimes, SavedEnergy, WeCanReuseIt, ByReusingIt],
  [3000, Base, RecycleTriangle, ThreeTimes, SavedEnergy, GreyWaterIsUsed, ByReusingIt],
  [
    500,
    Base,
    RecycleTriangle,
    ThreeTimes,
    SavedEnergy,
    GreyWaterIsUsed,
    ByReusingIt,
    GraphicShower,
  ],
  [
    500,
    Base,
    RecycleTriangle,
    ThreeTimes,
    SavedEnergy,
    GreyWaterIsUsed,
    ByReusingIt,
    GraphicShower,
    GraphicToilet,
  ],
  [
    3000,
    Base,
    RecycleTriangle,
    ThreeTimes,
    SavedEnergy,
    GreyWaterIsUsed,
    ByReusingIt,
    GraphicShower,
    GraphicToilet,
    GraphicBoatWash,
  ],
] as [duration: number, ...slides: (typeof Base)[]][];
