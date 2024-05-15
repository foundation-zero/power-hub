<template>
  <WidgetBase
    title="Water demand"
    unit="liter"
    :value="total"
    :format="formattedInt"
  >
    <StackedBarChart
      class="mt-3"
      :height="36"
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
  { icon: "mdi-recycle", color: "#86B4E8" },
  { icon: "mdi-water", color: "#00bcd4" },
];

const recycled = useRandomNumber(300, 2000);
const total = useRandomNumber(300, 2000);
</script>
