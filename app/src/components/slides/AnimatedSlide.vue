<template>
  <div :class="{ fade }">
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
const { fade } = defineProps<{ fade?: boolean | number }>();
</script>

<style scoped lang="scss">
svg {
  will-change: opacity;
  transition: opacity 750ms ease;
  opacity: 1;
}

.fade {
  &.slide-leave-to svg,
  &.slide-enter-from svg {
    opacity: 0;
  }
}
</style>
