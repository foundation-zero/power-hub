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
import MapLegend from "./presentation/MapLegend.vue";
import FZLogo from "./presentation/FZLogo.vue";
import InnerWaves from "./presentation/InnerWaves.vue";
import OuterWaves from "./presentation/OuterWaves.vue";
import PhaseLanes from "./presentation/PhaseLanes.vue";
import PipeLines from "./presentation/PipeLines.vue";
import PipeStreams from "./presentation/PipeStreams.vue";
import PowerHubComponents from "./presentation/PowerHubComponents.vue";

import { usePresentationStore } from "@/stores/presentation";
import { onMounted, onDeactivated } from "vue";
import { toRefs } from "vue";

const { start, stop } = usePresentationStore();
const { showWidgets, root } = toRefs(usePresentationStore());

onMounted(start);
onDeactivated(stop);
</script>
