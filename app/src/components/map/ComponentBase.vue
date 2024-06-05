<template>
  <g
    :id="component"
    ref="el"
    class="component"
    :class="state"
  >
    <svg
      :height="height"
      :width="width"
      :x="x"
      :y="y"
      :viewBox="viewBox"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <slot />
    </svg>
  </g>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { usePresentationStore } from "@/stores/presentation";
import type { PowerHubComponent } from "@/types/power-hub";
import { toRefs } from "vue";

const { component } = defineProps<{
  component: PowerHubComponent;
  width: string;
  height: string;
  x: string;
  y: string;
  viewBox: string;
}>();

const el = ref<HTMLElement>();
const { getComponentState, setPosition } = usePresentationStore();
const { root } = toRefs(usePresentationStore());

const state = computed(() => getComponentState(component));

onMounted(() => {
  if (!el.value) return;

  const svg = root.value!.getBoundingClientRect();

  const dx = 1920 / window.innerWidth;
  const dimensions = el.value.getBoundingClientRect();
  const x = dimensions.left + dimensions.width / 2;
  const y = dimensions.top + dimensions.height / 2;
  el.value.style.transformOrigin = `${x * dx}px ${(y - svg.top) * dx}px`;

  setPosition(component, { x, y: y - svg.top });
});
</script>

<style lang="scss">
$ttime: 750ms;

@keyframes pulse {
  50% {
    transform: scale(1.25, 1.25);
  }
  100% {
    transform: scale(1, 1);
  }
}

.component {
  transition: opacity 1500ms ease;
  will-change: transform, opacity;
  transform: scale(1, 1);
  opacity: 1;

  .fill,
  .text {
    transition:
      fill $ttime ease,
      stroke $ttime ease;

    will-change: fill, stroke;
  }

  &.highlighted {
    animation: pulse 750ms ease-out;
  }

  &.hidden {
    opacity: 0;
  }

  &:not(.active) {
    .fill[fill]:not([fill="white"]) {
      fill: rgba(229, 229, 229);
    }

    .fill[stroke]:not([stroke="white"]) {
      stroke: rgb(229, 229, 229);
    }

    .text[fill] {
      fill: #756b61;
    }
  }
}
</style>
