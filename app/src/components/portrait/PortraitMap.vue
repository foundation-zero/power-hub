<template>
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
</template>

<script setup lang="ts">
import PowerHubComponents from "@/components/portrait/map/PowerHubComponents.vue";
import InnerWaves from "@/components/portrait/map/InnerWaves.vue";
import PipeLines from "@/components/portrait/map/PipeLines.vue";
import PipeStreams from "@/components/portrait/map/PipeStreams.vue";
import { usePresentationStore } from "@/stores/presentation";
import { toRefs } from "vue";

const { root } = toRefs(usePresentationStore());
</script>
