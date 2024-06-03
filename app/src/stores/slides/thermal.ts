import Base from "@/components/slides/thermal/BaseThermal.vue";
import HowDoesItWork from "@/components/slides/thermal/HowDoesItWork.vue";
import HarvestingThermalEnergy from "@/components/slides/thermal/HarvestingThermalEnergy.vue";
import ZeroPercent from "@/components/slides/thermal/ZeroPercent.vue";
import HeatRadiation from "@/components/slides/thermal/HeatRadiation.vue";
import HeatTubes from "@/components/slides/thermal/HeatTubes.vue";
import HeatPipesGauge from "@/components/slides/thermal/HeatPipesGauge.vue";
import FiftyPercent from "@/components/slides/thermal/FiftyPercent.vue";
import EfficientAt from "@/components/slides/thermal/EfficientAt.vue";

export default [
  [500, Base],
  [500, Base, ZeroPercent],
  [5000, Base, HowDoesItWork, ZeroPercent],
  [2000, Base, HeatRadiation, HarvestingThermalEnergy, HeatTubes],
  [1000, Base, HeatRadiation, HarvestingThermalEnergy, HeatTubes, FiftyPercent],
  [1000, Base, HeatRadiation, HarvestingThermalEnergy, HeatTubes, FiftyPercent, EfficientAt],
  [
    700000,
    Base,
    HeatRadiation,
    HarvestingThermalEnergy,
    HeatTubes,
    FiftyPercent,
    EfficientAt,
    HeatPipesGauge,
  ],
] as [duration: number, ...slides: (typeof Base)[]][];
