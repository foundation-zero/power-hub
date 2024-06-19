<template>
  <v-main>
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
      <MapLegend
        v-show="showWidgets"
        transform="translate(167, 884)"
      />
      <FZLogo transform="translate(90, 107)" />
      <PipeLines />
      <PipeStreams />
      <Suspense>
        <PowerHubComponents />
      </Suspense>
    </svg>

    <Suspense>
      <WidgetsCarousel />
    </Suspense>
    <SlideShow />
  </v-main>
</template>

<script setup lang="ts">
import WidgetsCarousel from "../components/display/WidgetsCarousel.vue";
import SlideShow from "../components/display/SlideShow.vue";
import MapLegend from "../components/MapLegend.vue";
import FZLogo from "../components/FZLogo.vue";
import InnerWaves from "../components/landscape/map/InnerWaves.vue";
import OuterWaves from "../components/landscape/map/OuterWaves.vue";
import PhaseLanes from "../components/landscape/map/PhaseLanes.vue";
import PipeLines from "../components/landscape/map/PipeLines.vue";
import PipeStreams from "../components/landscape/map/PipeStreams.vue";
import PowerHubComponents from "../components/landscape/map/PowerHubComponents.vue";

import { usePresentationStore } from "@/stores/presentation";
import { onMounted, onDeactivated } from "vue";
import { toRefs } from "vue";

const { start, stop, setMode } = usePresentationStore();
const { showWidgets, root } = toRefs(usePresentationStore());

onMounted(() => setMode("display"));
onMounted(start);
onDeactivated(stop);
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: transform 750ms ease;
}

.fade-enter-from,
.fade-leave-to {
  transform: translateX(100%);
}
</style>
