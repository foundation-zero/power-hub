<template>
  <g :class="{ active: !showWaves }">
    <path
      opacity="0.4"
      d="M1968 534.003C1033.37 534.003 815.274 27.4376 252.03 -8.99707H128L187.5 -11.0612C209.527 -11.0612 231.019 -10.3562 252.03 -8.99707H1968V534.003Z"
      fill="#E9E9E9"
    />
    <path
      opacity="0.4"
      d="M1944 561.626C1114.37 561.626 1082.28 1087.49 87.229 1124.63H-26C-26 1124.63 -56 1126.69 -26 1126.69C13.0908 1126.69 50.8051 1125.99 87.229 1124.63H1944V561.626Z"
      fill="#E9E9E9"
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
