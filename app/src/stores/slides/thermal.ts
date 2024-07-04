import Base from "@/components/display/slides/thermal/BaseThermal.vue";
import HowDoesItWork from "@/components/display/slides/thermal/HowDoesItWork.vue";
import HarvestingThermalEnergy from "@/components/display/slides/thermal/HarvestingThermalEnergy.vue";
import ZeroPercent from "@/components/display/slides/thermal/ZeroToFiftyPercent.vue";
import HeatRadiation from "@/components/display/slides/thermal/HeatRadiation.vue";
import HeatPipesGauge from "@/components/display/slides/thermal/HeatPipesGauge.vue";
import ChillPowerGauge from "@/components/display/slides/thermal/ChillPower.vue";
import CompoundTemperature from "@/components/display/slides/thermal/CompoundTemperature.vue";
import BatteryGauge from "@/components/display/slides/thermal/BatteryGauge.vue";
import EfficientAt from "@/components/display/slides/thermal/EfficientAt.vue";
import StoringThermalEnergy from "@/components/display/slides/thermal/StoringThermalEnergy.vue";
import KiloWattHoursStored from "@/components/display/slides/thermal/KiloWattHoursStored.vue";
import HeatStored from "@/components/display/slides/thermal/HeatStored.vue";
import FromTheBattery from "@/components/display/slides/thermal/FromTheBattery.vue";
import BatteryGaugeOutline from "@/components/display/slides/thermal/BatteryGaugeOutline.vue";
import UsingAbsorption from "@/components/display/slides/thermal/UsingAbsorption.vue";
import SeventyPercent from "@/components/display/slides/thermal/SeventyPercent.vue";
import EfficientAtTurningHeatIntoCold from "@/components/display/slides/thermal/EfficientAtTurningHeatIntoCold.vue";
import ThisIsUsed from "@/components/display/slides/thermal/ThisIsUsed.vue";
import ThemeIcon from "@/components/display/slides/thermal/ThemeIcon.vue";
import StepByStep from "@/components/display/slides/StepByStep.vue";
import ThisIs from "@/components/display/slides/thermal/ThisIs.vue";
import WeUseThisTo from "@/components/display/slides/WeUseThisTo.vue";
import ThisProvides from "@/components/display/slides/thermal/ThisProvides.vue";
import ProcessCalledAbsorption from "@/components/display/slides/thermal/ProcessCalledAbsorption.vue";
import {
  activate,
  deactivate,
  decustomize,
  hide,
  highlight,
  mute,
  customize,
  show,
  startFlow,
  stopFlow,
  dehighlight,
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
  customize(heatTubes);
});

const decustomizeHeatPipes = actionFn(async ({ getComponentState }) => {
  const heatTubes = getComponentState("heat-tubes");
  decustomize(heatTubes);
});

const activateHeatBattery = actionFn(async ({ getComponentState, getFlow, sleep }) => {
  const heatBattery = getComponentState("heat-storage");
  const { streams } = getFlow("heat");

  activate(streams[1]);
  startFlow(streams[1]);

  await sleep(500);

  customize(heatBattery);
  startFlow(heatBattery);
  activate(heatBattery);
  highlight(heatBattery);

  await sleep(750);
});

const activateAbsorptionChiller = actionFn(async ({ getComponentState, getFlow, sleep }) => {
  const absorptionChiller = getComponentState("absorption-chiller");
  const { streams } = getFlow("heat");

  stopFlow(streams[1]);
  startFlow(streams[2]);
  activate(streams[2]);

  await sleep(500);

  activate(absorptionChiller);
  highlight(absorptionChiller);
});

const activateBattery = actionFn(async ({ getComponentState, sleep, getFlow }) => {
  const heatBattery = getComponentState("heat-storage");
  const battery = getComponentState("power-battery");
  const { streams } = getFlow("heat");

  stopFlow(streams[2]);
  stopFlow(heatBattery);
  activate(battery);
  highlight(battery);

  await sleep(750);
});

const deactivateHeatPipesAndBattery = actionFn(async ({ getComponentState, sleep }) => {
  const heatBattery = getComponentState("heat-storage");
  const heatPipes = getComponentState("heat-tubes");

  deactivate(heatBattery);
  deactivate(heatPipes);
  decustomize(heatBattery);

  await sleep(750);
});

const activateCompressionChiller = actionFn(async ({ getComponentState, getFlow, sleep }) => {
  const chiller = getComponentState("compression-chiller");
  const { streams } = getFlow("heat");

  activate(streams[4]);

  await sleep(500);

  activate(chiller);
  highlight(chiller);
  customize(chiller);

  await sleep(750);
});

const activateDemand = actionFn(async ({ getComponentState, getFlow, sleep }) => {
  const demand = getComponentState("cooling-demand");
  const { streams } = getFlow("heat");

  activate(streams[5]);

  await sleep(500);

  activate(demand);
  highlight(demand);
  customize(demand);
});

export default [
  ({ setJourney }) => setJourney("heat"),
  deactivateAll("heat"),
  [7000, ThemeIcon, ThisIs, WeUseThisTo],
  [0, ThemeIcon, ProcessCalledAbsorption],
  activateStream("heat"),
  [5000, ThemeIcon, StepByStep, ThisProvides],
  [0],
  toggleWidgets(false),
  hideAll("heat"),
  toggleWaves(false),
  [500, Base],
  [0, Base, HowDoesItWork],
  disableAll,
  activateHeatPipes,
  [750, Base, HeatRadiation, HeatPipesGauge],
  [1000, Base, HeatRadiation, HarvestingThermalEnergy, HeatPipesGauge],
  [1000, Base, HeatRadiation, HarvestingThermalEnergy, ZeroPercent, HeatPipesGauge],
  [7000, Base, HeatRadiation, HarvestingThermalEnergy, ZeroPercent, EfficientAt, HeatPipesGauge],
  decustomizeHeatPipes,
  [1000, Base],
  activateHeatBattery,
  [2000, Base, StoringThermalEnergy],
  [1000, Base, StoringThermalEnergy, KiloWattHoursStored],
  [1000, Base, StoringThermalEnergy, KiloWattHoursStored, HeatStored],
  [7000, Base, StoringThermalEnergy, KiloWattHoursStored, HeatStored, BatteryGauge],
  activateAbsorptionChiller,
  [7000, Base, FromTheBattery, KiloWattHoursStored, HeatStored, BatteryGauge, BatteryGaugeOutline],
  ({ getComponentState }) => dehighlight(getComponentState("absorption-chiller")),
  [1000, Base],
  [2000, Base, UsingAbsorption],
  [1000, Base, UsingAbsorption, SeventyPercent],
  [1000, Base, UsingAbsorption, SeventyPercent, EfficientAtTurningHeatIntoCold],
  [7000, Base, UsingAbsorption, SeventyPercent, EfficientAtTurningHeatIntoCold, ChillPowerGauge],
  [0, Base, ThisIsUsed, SeventyPercent, EfficientAtTurningHeatIntoCold],
  deactivateHeatPipesAndBattery,
  activateBattery,
  activateCompressionChiller,
  [0, Base, ThisIsUsed, SeventyPercent, EfficientAtTurningHeatIntoCold, CompoundTemperature],
  activateDemand,
  sleep(7000),
] as PresentationItem[];
