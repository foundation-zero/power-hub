<template>
  <svg
    width="100%"
    :viewBox="viewBox"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <InnerWaves />
    <OuterWaves />
    <PhaseLanes />
    <MapLegend transform="translate(167, 884)" />
    <foreignObject
      width="200"
      height="59"
      x="90"
      y="107"
    >
      <RouterLink
        to="/"
        xmlns="http://www.w3.org/1999/xhtml"
      >
        <FZLogo />
      </RouterLink>
    </foreignObject>

    <foreignObject
      x="1250"
      y="107"
      width="40"
      height="40"
    >
      <a
        href="https://www.foundationzero.org/insights/power-hub"
        xmlns="http://www.w3.org/1999/xhtml"
        target="_self"
      >
        <HomeIcon />
      </a>
    </foreignObject>

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

import MapLegend from "@/components/MapLegend.vue";
import FZLogo from "@/components/FZLogo.vue";
import InnerWaves from "./map/InnerWaves.vue";
import OuterWaves from "./map/OuterWaves.vue";
import PhaseLanes from "./map/PhaseLanes.vue";
import PipeLines from "./map/PipeLines.vue";
import PipeStreams from "./map/PipeStreams.vue";
import PowerHubComponents from "./map/PowerHubComponents.vue";
import HomeIcon from "../responsive/HomeIcon.vue";

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
