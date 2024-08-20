<template>
  <div class="d-flex justify-space-between no-pointer">
    <SwipeButton
      direction="left"
      class="with-pointer"
      :class="{ 'opacity-0': !swipeLeft, 'cursor-pointer': swipeLeft }"
      @click="swipeLeft && $emit('prev')"
    />
    <SwipeButton
      direction="right"
      class="with-pointer"
      :class="{ 'opacity-0': !swipeRight, 'cursor-pointer': swipeRight }"
      @click="swipeRight && $emit('next')"
    />
  </div>
</template>

<script setup lang="ts">
import SwipeButton from "./SwipeButton.vue";

defineProps<{ swipeLeft?: boolean; swipeRight?: boolean }>();
defineEmits(["prev", "next"]);
</script>

<style scoped lang="scss">
.swipe-button {
  transition: opacity 500ms ease;
  will-change: opacity;
}

.no-pointer {
  pointer-events: none;
}

.with-pointer {
  pointer-events: all;
}
</style>
