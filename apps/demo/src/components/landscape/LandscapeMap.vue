<template>
  <svg
    :viewBox="viewBox"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <InnerWaves />
    <OuterWaves />
    <PhaseLanes />
    <MapLegend transform="translate(167, 884)" />
    <PipeLines />
    <PipeStreams />
    <Suspense>
      <PowerHubComponents />
    </Suspense>
  </svg>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useDisplay } from "vuetify";

import MapLegend from "@demo/components/MapLegend.vue";

import InnerWaves from "./map/InnerWaves.vue";
import OuterWaves from "./map/OuterWaves.vue";
import PhaseLanes from "./map/PhaseLanes.vue";
import PipeLines from "./map/PipeLines.vue";
import PipeStreams from "./map/PipeStreams.vue";
import PowerHubComponents from "./map/PowerHubComponents.vue";

const PREFERRED_RATIO = 980 / 1600;

const display = useDisplay();

const width = computed(() => {
  if (display.height.value > display.width.value * PREFERRED_RATIO) {
    return Math.max(1350, display.width.value * (960 / display.height.value));
  }

  return 1600;
});

const viewBox = computed(() => `20 60 ${width.value} 980`);
</script>
