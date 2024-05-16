<template>
  <DisplayPresentation />
  <Suspense>
    <WidgetsCarousel />
  </Suspense>
  <SlideShow />
</template>

<script setup lang="ts">
import WidgetsCarousel from "../components/WidgetsCarousel.vue";
import DisplayPresentation from "../components/DisplayPresentation.vue";
import SlideShow from "@/components/SlideShow.vue";
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
