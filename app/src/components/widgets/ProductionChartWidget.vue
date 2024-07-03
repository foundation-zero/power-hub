<template>
  <v-card
    rounded="0"
    elevation="3"
    class="pt-4"
  >
    <div class="text-h6 text-uppercase font-weight-medium px-6">Production</div>
    <div class="background mt-3">
      <ChartLegend class="px-6 py-3" />
      <ProductionChart />
      <ConsumptionChart />
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
</script>

<style lang="scss" scoped>
.v-card {
  position: relative;
}

.background {
  background-color: #f9f8f8;
}
</style>
