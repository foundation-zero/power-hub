<template>
  <svg
    id="display-presentation"
    ref="root"
    width="100%"
    viewBox="0 0 1920 1080"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <InnerWaves />
    <OuterWaves />
    <PhaseLanes />
    <MapLegend v-show="showWidgets" />
    <FZLogo />
    <PipeLines />
    <PipeStreams />
    <Suspense>
      <PowerHubComponents />
    </Suspense>
  </svg>
</template>

<script setup lang="ts">
import MapLegend from "./map/MapLegend.vue";
import FZLogo from "./map/FZLogo.vue";
import InnerWaves from "./map/InnerWaves.vue";
import OuterWaves from "./map/OuterWaves.vue";
import PhaseLanes from "./map/PhaseLanes.vue";
import PipeLines from "./map/PipeLines.vue";
import PipeStreams from "./map/PipeStreams.vue";
import PowerHubComponents from "./map/PowerHubComponents.vue";

import { usePresentationStore } from "@/stores/presentation";
import { onMounted, onDeactivated } from "vue";
import { toRefs } from "vue";

const { start, stop } = usePresentationStore();
const { showWidgets, root } = toRefs(usePresentationStore());

onMounted(start);
onDeactivated(stop);
</script>
