<template>
  <div v-show="store.isRunning">
    <TransitionGroup name="slideshow">
      <v-img
        v-for="slide in store.slides"
        :key="slide"
        :src="slide"
        width="1920"
        height="1080"
      />
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@/stores/presentation";

const store = usePresentationStore();
</script>

<style scoped lang="scss">
div {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.v-img {
  position: absolute;
  top: 0;
  left: 0;
  will-change: opacity;
  transition: opacity 1000ms ease;
}

.slideshow-leave-to {
  opacity: 0;
}

.slideshow-enter-from {
  opacity: 0;
}
</style>
