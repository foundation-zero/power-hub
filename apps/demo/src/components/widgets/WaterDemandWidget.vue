<template>
  <WidgetBase
    title="Water demand"
    unit="liter"
    :value="waterDemand ?? 0"
    :format="formattedInt"
  >
    <StackedBarChart
      class="mt-3"
      :height="36"
      :values="[waterMakerOut ?? 0, (waterDemand ?? 0) - (waterMakerOut ?? 0)]"
      :series="series"
    />
  </WidgetBase>
</template>

<script setup lang="ts">
import WidgetBase from "./WidgetBase.vue";
import type { PowerHubStore } from "@shared/stores/power-hub";
import { formattedInt } from "@shared/utils/numbers";
import StackedBarChart, { type BarSeries } from "../graphs/FillBarChart.vue";
import { useObservable } from "@vueuse/rxjs";

const { powerHub } = defineProps<{
  powerHub: PowerHubStore;
}>();

const series: [BarSeries, BarSeries] = [
  { icon: "mdi-recycle", color: "#86B4E8" },
  { icon: "mdi-water", color: "#00bcd4" },
];

const waterDemand = useObservable(powerHub.sensors.useMean("freshWaterTank/waterDemandFlow"));
const waterMakerOut = useObservable(powerHub.sensors.useMean("waterMaker/productionFlow"));
</script>
