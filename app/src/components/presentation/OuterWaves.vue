<template>
  <g :class="{ active: !showWaves }">
    <path
      opacity="0.8"
      d="M1970 495.377C1000.5 495.377 742.5 -9.6871 130 -9.6871C130 -145.579 100.011 -198.902 68.8409 -217.623H0C0 -217.623 35.1124 -237.88 68.8409 -217.623H1970V495.377Z"
      fill="#F7F7F7"
    />
    <path
      opacity="0.6"
      d="M1946 541C976.5 541 1113 1106.06 6 1106.06C6 1198.7 2.78418 1248.68 -1.54163 1274H-24C-24 1274 -10.4283 1326.02 -1.54163 1274H1946V541Z"
      fill="#F3F3F3"
    />
  </g>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@/stores/presentation";
import { toRefs } from "vue";

const { showWaves } = toRefs(usePresentationStore());
</script>

<style lang="scss" scoped>
g {
  &.active > path {
    transform: scale(1, 1);
  }

  & > path {
    transition: transform 1500ms ease;
    will-change: transform;
    transform: scale(1, 0);
  }

  & :first-child {
    transform-origin: 50% 0%;
  }
  & :last-child {
    transform-origin: 50% 100%;
  }
}
</style>
