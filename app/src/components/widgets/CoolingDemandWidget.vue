<template>
  <WidgetBase
    title="Cooling demand"
    :unit="unit"
    :value="coolingDemand"
    :format="formattedInt"
  >
    <StackedBarChart
      class="mt-3"
      :height="20"
      :values="[chillPower ?? 0, compressionPower]"
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
import { computed } from "vue";
import { useAsWatts } from "@/utils";

const { powerHub } = defineProps<{
  powerHub: PowerHubStore;
}>();

const series: [BarSeries, BarSeries] = [
  { icon: "mdi-snowflake", color: "#ECD2D4" },
  { icon: "mdi-fan", color: "#C16A6F" },
];

const fillPower = useObservable(powerHub.sensors.useMean("cold_reservoir/fill_power"));
const chillPower = useObservable(powerHub.sensors.useMean("yazaki/chill_power"));

const compressionPower = computed(() => (fillPower.value ?? 0) - (chillPower.value ?? 0));

const { unit, value: coolingDemand } = useAsWatts(fillPower, 10000);
</script>
