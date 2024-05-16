<template>
  <v-card
    rounded="0"
    elevation="3"
    class="pt-4 pb-10"
  >
    <div class="text-h6 text-uppercase font-weight-medium px-6">Production</div>
    <ProductionChart class="mt-5" />
    <DailyWeather />
  </v-card>
</template>

<script setup lang="ts">
import DailyWeather from "../DayNightCycle.vue";
import ProductionChart from "../graphs/ProductionChart.vue";
</script>

<style lang="scss" scoped>
.v-card {
  position: relative;
}
</style>
