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
      :disabled="!absorptionPower && !compressionPower"
      :values="[absorptionPower ?? 0, compressionPower ?? 0]"
      :series="series"
    />
  </WidgetBase>
</template>

<script setup lang="ts">
import WidgetBase from "./WidgetBase.vue";
import type { PowerHubStore } from "@shared/stores/power-hub";
import { formattedInt, negateAndClampAtZero } from "@shared/utils/numbers";
import StackedBarChart, { type BarSeries } from "../graphs/FillBarChart.vue";
import { useObservable } from "@vueuse/rxjs";
import { useAsWatts } from "@shared/utils";
import { map } from "rxjs";

const { powerHub } = defineProps<{
  powerHub: PowerHubStore;
}>();

const series: [BarSeries, BarSeries] = [
  { icon: "mdi-snowflake", color: "#ECD2D4" },
  { icon: "mdi-fan", color: "#C16A6F" },
];

const fillPower = useObservable(powerHub.sensors.useMean("coldReservoir/coolingSupply"));
const absorptionPower = useObservable(
  powerHub.sensors.useMean("yazaki/chillPower").pipe(map(negateAndClampAtZero)),
);

const compressionPower = useObservable(
  powerHub.sensors.useMean("chiller/chillPower").pipe(map(negateAndClampAtZero)),
);

const { unit, value: coolingDemand } = useAsWatts(fillPower, 10000);
</script>
