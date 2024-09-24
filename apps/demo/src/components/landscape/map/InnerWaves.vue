<template>
  <g :class="{ active: showWaves }">
    <path
      d="M1720 558.753C651.961 558.753 806 251 128 251V844H218.82C829 844 412.197 558.753 1720 558.753Z"
      fill="#F5F5F5"
    />

    <path
      d="M1740 558.251C671.961 558.251 822.721 379 78 379V706H168.82C899.918 686.97 432.197 558.251 1740 558.251Z"
      fill="#EBEBEB"
    />

    <path
      d="M1537 556.232C894.434 556.232 670 120 197 120L197.66 978C674.5 978 1177.5 556.232 1537 556.232Z"
      fill="#D9D9D9"
      fill-opacity="0.3"
    />
  </g>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@demo/stores/presentation";
import { toRefs } from "vue";

const { showWaves } = toRefs(usePresentationStore());
</script>

<style lang="scss" scoped>
g {
  & > path {
    will-change: transform;
    transition: transform 1000ms ease;
    transform: scale(1, 0);
    transform-origin: 0% 50%;
  }

  & :first-child {
    transition-delay: 250ms;
  }

  & :nth-child(2) {
    transition-delay: 500ms;
  }

  &.active > path {
    transform: scale(1, 1);
  }
}
</style>
