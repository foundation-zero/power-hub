<template>
  <g
    id="pipe-lines"
    :class="pipes"
  >
    <path
      d="M275 697L475 697L608 766.5M608 766.5H1003.5L815.5 858.5L608 766.5Z"
      stroke="white"
      stroke-width="18"
    />
    <path
      :class="{ muted: pipes.muted }"
      d="M319.958 495.104L430.561 563.455"
      stroke="white"
      stroke-width="18"
    />
    <path
      :class="{ muted: pipes.muted }"
      d="M426 562L523.5 562L621 562"
      stroke="white"
      stroke-width="18"
    />
    <path
      :class="{ muted: pipes.muted }"
      d="M958 581.001L982 581.001L1136 581.001"
      stroke="white"
      stroke-width="18"
    />
    <path
      :class="{ muted: pipes.muted }"
      d="M765.008 494.264L965.414 581.595"
      stroke="white"
      stroke-width="18"
    />
    <path
      :class="{ muted: pipes.muted }"
      d="M613.372 562.271L816.454 653.753"
      stroke="white"
      stroke-width="18"
    />
    <path
      :class="{ muted: pipes.muted }"
      d="M970.9 579.942L814.492 656.326"
      stroke="white"
      stroke-width="18"
    />
    <path
      :class="{ muted: pipes.muted }"
      d="M259 494H319"
      stroke="white"
      stroke-width="18"
    />
    <path
      :class="{ muted: pipes.muted }"
      d="M611 429L772 496.5"
      stroke="white"
      stroke-width="4"
    />
    <path
      d="M318.94 494.35L437.179 421.591"
      stroke="white"
      stroke-width="18"
    />
    <path
      d="M259 494H319"
      stroke="white"
      stroke-width="18"
    />
    <path
      d="M432 423L1038 422"
      stroke="white"
      stroke-width="18"
    />
  </g>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@demo/stores/presentation";
import { toRefs } from "vue";

const { pipes } = toRefs(usePresentationStore());
</script>

<style lang="scss" scoped>
#pipe-lines {
  & > path {
    will-change: stroke-width, opacity, stroke;
    transition:
      stroke-width 750ms ease,
      stroke 750ms ease,
      opacity 750ms ease;
  }

  &:not(.active) > path:not(.muted) {
    opacity: 0;
    stroke-width: 0;
  }
}

path.muted {
  opacity: 1;
  stroke: rgba(229, 229, 229);
  stroke-width: 4;
}
</style>
