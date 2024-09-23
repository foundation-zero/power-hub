<template>
  <TextSlide journey="heat">
    <template #title>Harvesting thermal energy from the sun using heat pipes</template>
    <template #body>
      <HeatPipesGauge
        width="100%"
        :height="undefined"
      />
      <p class="font-weight-bold">
        We use heat pipes to harvest thermal energy (i.e. heat) from the sun. Heat pipes are glass
        tubes which hold a vacuum. Inside that vacuum there is a bit of liquid, often distilled
        water. This way the sunlight can pass through the glass and heat up that medium, but the
        heat from the medium can't escape because it's insulated by the vacuum.
      </p>

      <p>
        That heat then causes the medium to evaporate and move up to the collection point. There the
        heat is exchanged and the medium condenses to be heated again. We pass glycol along the
        collection point to move the heat into the Power Hub.
      </p>
    </template>
  </TextSlide>
</template>

<script setup lang="ts">
import HeatPipesGauge from "@/components/gauges/HeatPipesGauge.vue";
import TextSlide from "../../TextSlide.vue";
</script>
