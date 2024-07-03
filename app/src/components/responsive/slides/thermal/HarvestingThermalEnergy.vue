<template>
  <TextSlide journey="heat">
    <template #title>Harvesting thermal energy from the sun using heat tubes</template>
    <template #body>
      <HeatPipesGauge
        width="100%"
        :height="undefined"
      />
    </template>
  </TextSlide>
</template>

<script setup lang="ts">
import HeatPipesGauge from "@/components/gauges/HeatPipesGauge.vue";
import TextSlide from "../../TextSlide.vue";
</script>
