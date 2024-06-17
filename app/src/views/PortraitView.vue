<template>
  <v-layout>
    <AppBar />

    <v-main>
      <div
        class="d-flex flex-column justify-end align-center pt-5 px-3"
        style="height: calc(100vh - 64px)"
      >
        <svg
          id="portrait-view"
          ref="root"
          viewBox="0 0 321 744"
          width="100%"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <InnerWaves />
          <PipeLines />
          <PipeStreams />
          <PowerHubComponents />
        </svg>
      </div>
    </v-main>

    <ContentPanel v-model:modelValue="show">
      <JourneyContent />
    </ContentPanel>
  </v-layout>
</template>

<script setup lang="ts">
import PowerHubComponents from "../components/portrait/map/PowerHubComponents.vue";
import InnerWaves from "../components/portrait/map/InnerWaves.vue";
import PipeLines from "../components/portrait/map/PipeLines.vue";
import PipeStreams from "@/components/portrait/map/PipeStreams.vue";

import { usePresentationStore } from "@/stores/presentation";
import { toRefs } from "vue";
import ContentPanel from "@/components/portrait/ContentPanel.vue";
import AppBar from "@/components/portrait/AppBar.vue";
import JourneyContent from "@/components/responsive/JourneyContent.vue";
import { computed } from "vue";

const { setJourney } = usePresentationStore();
const { root, currentJourney } = toRefs(usePresentationStore());

const show = computed({
  get() {
    return !!currentJourney.value;
  },
  set(val: boolean) {
    if (!val) {
      setJourney();
    }
  },
});
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
