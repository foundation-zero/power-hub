import Base from "@/components/slides/thermal/BaseThermal.vue";
import HowDoesItWork from "@/components/slides/thermal/HowDoesItWork.vue";
import HarvestingThermalEnergy from "@/components/slides/thermal/HarvestingThermalEnergy.vue";
import ZeroPercent from "@/components/slides/thermal/ZeroPercent.vue";
import HeatRadiation from "@/components/slides/thermal/HeatRadiation.vue";
import HeatTubes from "@/components/slides/thermal/HeatTubes.vue";
import HeatPipesGauge from "@/components/slides/thermal/HeatPipesGauge.vue";
import ChillPowerGauge from "@/components/slides/thermal/ChillPower.vue";
import CompoundTemperature from "@/components/slides/thermal/CompoundTemperature.vue";
import BatteryGauge from "@/components/slides/thermal/BatteryGauge.vue";
import FiftyPercent from "@/components/slides/thermal/FiftyPercent.vue";
import EfficientAt from "@/components/slides/thermal/EfficientAt.vue";
import StoringThermalEnergy from "@/components/slides/thermal/StoringThermalEnergy.vue";
import KiloWattHoursStored from "@/components/slides/thermal/KiloWattHoursStored.vue";
import HeatStored from "@/components/slides/thermal/HeatStored.vue";
import FromTheBattery from "@/components/slides/thermal/FromTheBattery.vue";
import BatteryGaugeOutline from "@/components/slides/thermal/BatteryGaugeOutline.vue";
import UsingAbsorption from "@/components/slides/thermal/UsingAbsorption.vue";
import SeventyPercent from "@/components/slides/thermal/SeventyPercent.vue";
import EfficientAtTurningHeatIntoCold from "@/components/slides/thermal/EfficientAtTurningHeatIntoCold.vue";
import { activate, deactivate } from "@/utils";
import type { PresentationItem } from "@/types";
import {
  actionFn,
  activateStream,
  deactivateAll,
  hideAll,
  showAll,
  sleep,
  toggleWaves,
  toggleWidgets,
} from "./actions";

const disableAllExceptHeatPipes = actionFn(({ getFlow, getComponentState }) => {
  const { streams, components } = getFlow("heat");

  components.forEach(deactivate);
  activate(getComponentState("heat-tubes"));
  activate(getComponentState("sun"));
});

export default [
  ({ setJourney }) => setJourney("heat"),
  showAll,
  toggleWaves(true),
  toggleWidgets(true),
  deactivateAll("heat"),
  activateStream("heat"),
  sleep(3000),
  toggleWidgets(false),
  hideAll("heat"),
  toggleWaves(false),
  [500, Base],
  [500, Base, ZeroPercent],
  [5000, Base, HowDoesItWork, ZeroPercent],
  disableAllExceptHeatPipes,
  [2000, Base, HeatRadiation, HarvestingThermalEnergy, HeatTubes],
  [1000, Base, HeatRadiation, HarvestingThermalEnergy, HeatTubes, FiftyPercent],
  [1000, Base, HeatRadiation, HarvestingThermalEnergy, HeatTubes, FiftyPercent, EfficientAt],
  [
    7000,
    Base,
    HeatRadiation,
    HarvestingThermalEnergy,
    HeatTubes,
    FiftyPercent,
    EfficientAt,
    HeatPipesGauge,
  ],
  [1000, Base],
  [2000, Base, StoringThermalEnergy],
  [1000, Base, StoringThermalEnergy, KiloWattHoursStored],
  [1000, Base, StoringThermalEnergy, KiloWattHoursStored, HeatStored],
  [7000, Base, StoringThermalEnergy, KiloWattHoursStored, HeatStored, BatteryGauge],
  [7000, Base, FromTheBattery, KiloWattHoursStored, HeatStored, BatteryGauge, BatteryGaugeOutline],
  [1000, Base],
  [2000, Base, UsingAbsorption],
  [1000, Base, UsingAbsorption, SeventyPercent],
  [1000, Base, UsingAbsorption, SeventyPercent, EfficientAtTurningHeatIntoCold],
  [7000, Base, UsingAbsorption, SeventyPercent, EfficientAtTurningHeatIntoCold, ChillPowerGauge],
  [1000, Base],
] as PresentationItem[];
