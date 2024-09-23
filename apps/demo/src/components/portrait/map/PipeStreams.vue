<template>
  <g>
    <path
      d="M105.5 52L59.5 166.5L59.5 266.5L59.5 545"
      stroke="#F9E297"
      stroke-width="4"
      :class="journeys.electrical.streams[0]"
    />
    <path
      d="M119.5 52L165.5 166.5L165.5 266.5L165.5 342"
      stroke="#DCACB0"
      stroke-width="4"
      :class="journeys.heat.streams[0]"
    />
    <path
      d="M220.5 52L266.5 166.5L266.5 266.5L266.5 545"
      stroke="#4A8AD2"
      stroke-width="4"
      :class="journeys.water.streams[0]"
    />
    <path
      d="M60.5 298.5L164.5 492.5"
      stroke="#FFF3CB"
      stroke-width="4"
      :class="journeys.heat.streams[0]"
    />

    <path
      d="M165.5 582L165.5 516.5L165.5 416.5"
      stroke="#AFE7EB"
      stroke-width="4"
      :class="journeys.heat.streams[0]"
    />
  </g>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@/stores/presentation";

const { journeys } = usePresentationStore();
</script>

<style lang="scss" scoped>
$ttime: 750ms;

path {
  will-change: stroke-dashoffset, opacity, stroke;
  transition:
    opacity $ttime ease,
    stroke $ttime ease;

  &.hidden {
    opacity: 0;
  }
}
</style>
