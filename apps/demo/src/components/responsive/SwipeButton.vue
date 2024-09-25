<template>
  <svg
    width="100"
    height="100"
    viewBox="0 0 100 100"
    fill="none"
    :transform="`rotate(${rotation})`"
    class="swipe-button"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      opacity="0.5"
      cx="49.8064"
      cy="49.8064"
      r="49.8064"
      transform="matrix(-1 -8.74228e-08 -8.74228e-08 1 100 0)"
      fill="white"
    />
    <circle
      cx="38.4581"
      cy="38.4581"
      r="38.4581"
      transform="matrix(-1 -8.74228e-08 -8.74228e-08 1 88.6514 11.3496)"
      fill="white"
    />
    <rect
      width="7.56553"
      height="27.7403"
      transform="matrix(0.707107 0.707107 0.707107 -0.707107 40.7368 64.1445)"
      fill="black"
    />
    <rect
      width="7.56553"
      height="27.7403"
      transform="matrix(-0.707107 0.707107 0.707107 0.707107 46.0864 30.2637)"
      fill="black"
    />
  </svg>
</template>

<script setup lang="ts">
import type { Direction } from "@demo/types";

import { computed } from "vue";
const { direction } = defineProps<{ direction: Direction }>();

const rotation = computed(() => (direction === "left" ? 180 : 0));
</script>
