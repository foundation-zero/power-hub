<template>
  <svg
    id="portrait-view"
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
import PowerHubComponents from "@demo/components/portrait/map/PowerHubComponents.vue";
import InnerWaves from "@demo/components/portrait/map/InnerWaves.vue";
import PipeLines from "@demo/components/portrait/map/PipeLines.vue";
import PipeStreams from "@demo/components/portrait/map/PipeStreams.vue";
</script>
