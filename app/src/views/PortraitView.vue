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

    <ContentPanel />
  </v-layout>
</template>

<script setup lang="ts">
import PowerHubComponents from "../components/map/portrait/PowerHubComponents.vue";
import InnerWaves from "../components/map/portrait/InnerWaves.vue";
import PipeLines from "../components/map/portrait/PipeLines.vue";
import PipeStreams from "@/components/map/portrait/PipeStreams.vue";

import { usePresentationStore } from "@/stores/presentation";
import { toRefs } from "vue";
import ContentPanel from "@/components/portrait/ContentPanel.vue";
import AppBar from "@/components/portrait/AppBar.vue";

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
