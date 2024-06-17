<template>
  <v-layout>
    <v-main>
      <div
        class="d-flex flex-column justify-center align-center"
        style="height: 100vh"
      >
        <svg
          id="landscape-view"
          ref="root"
          width="100%"
          :viewBox="viewBox"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <InnerWaves />
          <OuterWaves />
          <PhaseLanes />
          <MapLegend transform="translate(167, 884)" />
          <FZLogo transform="translate(90, 107)" />
          <PipeLines />
          <PipeStreams />
          <Suspense>
            <PowerHubComponents />
          </Suspense>
        </svg>
      </div>
    </v-main>
    <ContentPanel />
  </v-layout>
</template>

<script setup lang="ts">
import MapLegend from "../components/MapLegend.vue";
import FZLogo from "../components/FZLogo.vue";
import InnerWaves from "../components/landscape/map/InnerWaves.vue";
import OuterWaves from "../components/landscape/map/OuterWaves.vue";
import PhaseLanes from "../components/landscape/map/PhaseLanes.vue";
import PipeLines from "../components/landscape/map/PipeLines.vue";
import PipeStreams from "../components/landscape/map/PipeStreams.vue";
import PowerHubComponents from "../components/landscape/map/PowerHubComponents.vue";

import { usePresentationStore } from "@/stores/presentation";
import { toRefs } from "vue";
import { useDisplay } from "vuetify";
import { computed } from "vue";
import ContentPanel from "@/components/landscape/ContentPanel.vue";

const display = useDisplay();
const PREFERRED_RATIO = 980 / 1600;

const width = computed(() => {
  if (display.height.value > display.width.value * PREFERRED_RATIO) {
    return Math.max(1350, display.width.value * (960 / display.height.value));
  }

  return 1600;
});

const viewBox = computed(() => {
  return `20 60 ${width.value} 980`;
});

const { root } = toRefs(usePresentationStore());
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
