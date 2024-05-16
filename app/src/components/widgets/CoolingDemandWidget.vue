<template>
  <WidgetBase
    title="Cooling demand"
    unit="kWh"
    :value="total + recycled"
    :format="formattedInt"
  >
    <StackedBarChart
      class="mt-3"
      :height="20"
      :values="[recycled, total]"
      :series="series"
    />
  </WidgetBase>
</template>

<script setup lang="ts">
import WidgetBase from "./WidgetBase.vue";
import type { PowerHubStore } from "@/stores/power-hub";
import { formattedInt, useRandomNumber } from "@/utils/numbers";
import StackedBarChart, { type BarSeries } from "../graphs/FillBarChart.vue";

defineProps<{
  powerHub: PowerHubStore;
}>();

const series: [BarSeries, BarSeries] = [
  { icon: "mdi-snowflake", color: "#ECD2D4" },
  { icon: "mdi-fan", color: "#C16A6F" },
];

const recycled = useRandomNumber(30, 200);
const total = useRandomNumber(30, 200);
</script>
