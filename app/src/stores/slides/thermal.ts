import Base from "@/components/slides/thermal/BaseThermal.vue";
import HowDoesItWork from "@/components/slides/thermal/HowDoesItWork.vue";
import HarvestingThermalEnergy from "@/components/slides/thermal/HarvestingThermalEnergy.vue";
import ZeroPercent from "@/components/slides/thermal/ZeroPercent.vue";
import HeatRadiation from "@/components/slides/thermal/HeatRadiation.vue";
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
import {
  activate,
  dash,
  deactivate,
  deoutline,
  hide,
  highlight,
  mute,
  outline,
  show,
  startFlow,
  stopFlow,
  undash,
} from "@/utils";
import type { PresentationItem } from "@/types";
import {
  actionFn,
  activateStream,
  deactivateAll,
  hideAll,
  sleep,
  toggleWaves,
  toggleWidgets,
} from "./actions";
import ThisIsUsed from "@/components/slides/thermal/ThisIsUsed.vue";

const disableAll = actionFn(async ({ sleep, getFlow, pipes, getComponentState }) => {
  const sun = getComponentState("sun");
  const { streams, components } = getFlow("heat");

  components.forEach(deactivate);
  activate(sun);
  streams.forEach(hide);
  mute(pipes);

  await sleep(750);

  streams.forEach(deactivate);
  streams.forEach(show);

  highlight(sun);
  await sleep(750);
});

const activateHeatPipes = actionFn(async ({ getFlow, getComponentState, sleep }) => {
  const heatTubes = getComponentState("heat-tubes");
  const { streams } = getFlow("heat");

  activate(streams[0]);

  await sleep(500);

  activate(heatTubes);
  outline(heatTubes);
});

const deactivateHeatPipes = actionFn(async ({ getComponentState }) => {
  const heatTubes = getComponentState("heat-tubes");
  deoutline(heatTubes);
});

const activateHeatBattery = actionFn(async ({ getComponentState, getFlow, sleep }) => {
  const heatBattery = getComponentState("heat-storage");
  const { streams } = getFlow("heat");

  activate(streams[1]);
  startFlow(streams[1]);

  await sleep(500);

  outline(heatBattery);
  dash(heatBattery);
  activate(heatBattery);
  highlight(heatBattery);

  await sleep(750);
});

const activateAbsorptionChiller = actionFn(async ({ getComponentState, getFlow, sleep }) => {
  const heatBattery = getComponentState("heat-storage");
  const absorptionChiller = getComponentState("absorption-chiller");
  const { streams } = getFlow("heat");

  undash(heatBattery);
  stopFlow(streams[1]);
  startFlow(streams[2]);
  activate(streams[2]);

  await sleep(750);

  activate(absorptionChiller);
  highlight(absorptionChiller);
});

const triggerAbsorptionChiller = actionFn(({ getComponentState }) => {
  const absorptionChiller = getComponentState("absorption-chiller");

  outline(absorptionChiller);
});

const activateBattery = actionFn(async ({ getComponentState, sleep, getFlow }) => {
  const battery = getComponentState("power-battery");
  const { streams } = getFlow("heat");

  stopFlow(streams[2]);
  activate(battery);

  await sleep(750);
});

const activateCompressionChiller = actionFn(async ({ getComponentState, getFlow, sleep }) => {
  const chiller = getComponentState("compression-chiller");
  const { streams } = getFlow("heat");

  activate(streams[4]);

  await sleep(750);

  activate(chiller);
  highlight(chiller);
  outline(chiller);

  await sleep(750);
});

const activateDemand = actionFn(async ({ getComponentState, getFlow, sleep }) => {
  const demand = getComponentState("cooling-demand");
  const { streams } = getFlow("heat");

  activate(streams[5]);
  outline(streams[5]);

  await sleep(750);

  activate(demand);
  highlight(demand);
  outline(demand);
});

export default [
  ({ setJourney }) => setJourney("heat"),
  deactivateAll("heat"),
  activateStream("heat"),
  sleep(3000),
  toggleWidgets(false),
  hideAll("heat"),
  toggleWaves(false),
  [500, Base],
  [500, Base, ZeroPercent],
  [5000, Base, HowDoesItWork, ZeroPercent],
  disableAll,
  activateHeatPipes,
  [2000, Base, HeatRadiation, HarvestingThermalEnergy],
  [1000, Base, HeatRadiation, HarvestingThermalEnergy, FiftyPercent],
  [1000, Base, HeatRadiation, HarvestingThermalEnergy, FiftyPercent, EfficientAt],
  [7000, Base, HeatRadiation, HarvestingThermalEnergy, FiftyPercent, EfficientAt, HeatPipesGauge],
  deactivateHeatPipes,
  [1000, Base],
  activateHeatBattery,
  [2000, Base, StoringThermalEnergy],
  [1000, Base, StoringThermalEnergy, KiloWattHoursStored],
  [1000, Base, StoringThermalEnergy, KiloWattHoursStored, HeatStored],
  [7000, Base, StoringThermalEnergy, KiloWattHoursStored, HeatStored, BatteryGauge],
  activateAbsorptionChiller,
  [7000, Base, FromTheBattery, KiloWattHoursStored, HeatStored, BatteryGauge, BatteryGaugeOutline],
  [1000, Base],
  triggerAbsorptionChiller,
  [2000, Base, UsingAbsorption],
  [1000, Base, UsingAbsorption, SeventyPercent],
  [1000, Base, UsingAbsorption, SeventyPercent, EfficientAtTurningHeatIntoCold],
  [7000, Base, UsingAbsorption, SeventyPercent, EfficientAtTurningHeatIntoCold, ChillPowerGauge],
  [0, Base, ThisIsUsed, SeventyPercent, EfficientAtTurningHeatIntoCold],
  activateBattery,
  activateCompressionChiller,
  activateDemand,
  [7000, Base, ThisIsUsed, SeventyPercent, EfficientAtTurningHeatIntoCold, CompoundTemperature],
  [1000, Base],
] as PresentationItem[];
