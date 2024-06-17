<template>
  <div :class="{ fade, delay }">
    <svg
      width="1920"
      height="1080"
      viewBox="0 0 1920 1080"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <slot />
    </svg>
  </div>
</template>

<script lang="ts" setup>
defineProps<{ fade?: boolean | number; delay?: boolean | number }>();
</script>

<style scoped lang="scss">
.slide-enter-active,
.slide-leave-active {
  will-change: opacity;
  transition: opacity 750ms ease;
  opacity: 1;
}

.fade {
  &.slide-leave-to,
  &.slide-enter-from {
    opacity: 0;
  }
}

.slide-enter-active.delay {
  transition-delay: 750ms;
}
</style>
