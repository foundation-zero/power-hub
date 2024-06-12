<template>
  <WidgetBase
    title="Water demand"
    unit="liter"
    :value="waterDemand"
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
import type { PowerHubStore } from "@/stores/power-hub";
import { formattedInt } from "@/utils/numbers";
import StackedBarChart, { type BarSeries } from "../graphs/FillBarChart.vue";
import { useObservable } from "@vueuse/rxjs";

const { powerHub } = defineProps<{
  powerHub: PowerHubStore;
}>();

const series: [BarSeries, BarSeries] = [
  { icon: "mdi-recycle", color: "#86B4E8" },
  { icon: "mdi-water", color: "#00bcd4" },
];

const waterDemand = useObservable(powerHub.sensors.useMean("fresh_water_tank/water_demand"));
const waterMakerOut = useObservable(powerHub.sensors.useMean("water_maker/out_flow"));
</script>
