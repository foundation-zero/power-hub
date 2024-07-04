<template>
  <svg
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
    <FZLogo
      transform="translate(90, 107)"
      @click="showIntro"
    />
    <HomeIcon
      transform="translate(1250, 107)"
      @click="goToFZeroWebsite"
    />

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
import { usePresentationStore } from "@/stores/presentation";
import { toRefs } from "vue";
import { useRouter } from "vue-router";
import HomeIcon from "../responsive/HomeIcon.vue";

const router = useRouter();

const PREFERRED_RATIO = 980 / 1600;

const display = useDisplay();

const { root } = toRefs(usePresentationStore());

const width = computed(() => {
  if (display.height.value > display.width.value * PREFERRED_RATIO) {
    return Math.max(1350, display.width.value * (960 / display.height.value));
  }

  return 1600;
});

const showIntro = () => router.push("/");
const goToFZeroWebsite = () =>
  window.open("https://www.foundationzero.org/insights/power-hub", "_self");
const viewBox = computed(() => `20 60 ${width.value} 980`);
</script>
