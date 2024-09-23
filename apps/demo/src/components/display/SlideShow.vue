<template>
  <TransitionGroup
    v-if="store.isRunning"
    name="slide"
  >
    <component
      :is="slide"
      v-for="slide in store.slides"
      :key="slide.name"
      class="slide"
    />
  </TransitionGroup>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@/stores/presentation";

const store = usePresentationStore();
</script>

<style scoped lang="scss">
.slide {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style>
