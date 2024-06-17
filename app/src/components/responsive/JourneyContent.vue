<template>
  <h5 class="text-h5">Thermal energy</h5>

  <v-divider class="mt-3 w-100" />

  <carousel
    :items-to-show="1"
    class="w-100 mt-3 flex-grow-1"
  >
    <slide
      v-for="slide in 3"
      :key="slide"
    >
      <v-sheet
        width="100%"
        class="text-left"
      >
        <p class="text-h6">From the battery we feed heat into the absorption chiller....</p>
        <BatteryGauge
          width="100%"
          class="mt-5"
        />
      </v-sheet>
    </slide>
  </carousel>
</template>

<script setup lang="ts">
import { Carousel, Slide } from "vue3-carousel";
import BatteryGauge from "../gauges/BatteryGauge.vue";
</script>
