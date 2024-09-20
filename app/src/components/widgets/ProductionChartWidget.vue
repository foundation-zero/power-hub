<template>
  <v-card
    rounded="0"
    elevation="3"
    class="pt-4"
  >
    <div class="text-h6 text-uppercase font-weight-medium px-6">Electrical</div>
    <div class="background mt-3">
      <ChartLegend class="px-6 py-3" />
      <ProductionChart
        :data="productionPerTwoHours"
        :max="max"
      />
      <ConsumptionChart
        :data="consumptionPerTwoHours"
        :max="max"
      />
      <TimeScale class="mb-10 mx-10" />
      <DayNightCycle class="px-6" />
    </div>
  </v-card>
</template>

<script setup lang="ts">
import DayNightCycle from "../DayNightCycle.vue";
import ProductionChart from "../graphs/ProductionChart.vue";
import ConsumptionChart from "../graphs/ConsumptionChart.vue";
import ChartLegend from "../ChartLegend.vue";
import TimeScale from "../TimeScale.vue";
import { useObservable } from "@vueuse/rxjs";
import { useCombinedHourlyData } from "@/utils";
import { usePowerHubStore } from "@/stores/power-hub";
import { todayRangeFn } from "@/utils/numbers";
import { map } from "rxjs";
import { toHourlyData } from "@/api";
import { range } from "lodash";
import { computed } from "vue";

const { sum } = usePowerHubStore();

const hours = range(0, 24, 1);

const consumptionPerTwoHours = useObservable(
  useCombinedHourlyData(
    sum
      .useOverTime("electric/power/consumption", todayRangeFn)
      .pipe(map((values) => values.map(toHourlyData))),
    sum.useMeanPerHourOfDay("electric/power/consumption"),
    1,
    hours,
  ),
);

const productionPerTwoHours = useObservable(
  useCombinedHourlyData(
    sum
      .useOverTime("electric/power/production", todayRangeFn)
      .pipe(map((values) => values.map(toHourlyData))),
    sum.useMeanPerHourOfDay("electric/power/production"),
    1,
    hours,
  ),
);

const max = computed(() => {
  const maxProduction =
    productionPerTwoHours.value?.reduce((max, val) => Math.max(max, val.value), 0) ?? 0;
  const maxConsumption =
    consumptionPerTwoHours.value?.reduce((max, val) => Math.max(max, val.value), 0) ?? 0;

  return Math.max(maxProduction, maxConsumption);
});
</script>

<style lang="scss" scoped>
.v-card {
  position: relative;
}

.background {
  background-color: #f9f8f8;
}
</style>
