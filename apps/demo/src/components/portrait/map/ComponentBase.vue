<template>
  <g
    ref="el"
    class="component portrait"
    :class="state"
    @mouseenter="onHover"
    @mouseleave="onLeave"
    @touchstart="onTouch"
    @click="onClick"
    @touchend="onLeave"
  >
    <slot />
  </g>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { usePresentationStore } from "@/stores/presentation";
import type { PowerHubComponent } from "@/types/power-hub";
import type { Journey } from "@/types";
import { activate, deactivate, dehighlight, hide, highlight, show } from "@/utils";
import { ref } from "vue";
import { toRefs } from "vue";
import { useRouter } from "vue-router";

const { component, journey } = defineProps<{
  component: PowerHubComponent;
  journey: Journey;
}>();

const el = ref<SVGElement>();
const router = useRouter();
const { getComponentState, getFlow, streamStates, componentStates } = usePresentationStore();
const { currentJourney } = toRefs(usePresentationStore());

const state = computed(() => getComponentState(component));
const touched = ref(false);

const onHover = () => {
  const { streams, components } = getFlow(journey);

  componentStates.forEach(deactivate);
  streamStates.forEach(hide);

  components.forEach(activate);
  components.forEach(highlight);
  streams.forEach(show);

  setTimeout(() => components.forEach(dehighlight), 750);
};

const onTouch = () => {
  touched.value = true;
  onHover();
  setTimeout(() => {
    router.push(`/journeys/${journey}`);
    touched.value = false;
  }, 500);
};

const onClick = () => {
  if (touched.value) return;

  router.push(`/journeys/${journey}`);
};

const onLeave = () => {
  if (currentJourney.value) return;

  streamStates.forEach(show);
  componentStates.forEach(activate);
};
</script>

<style lang="scss">
$ttime: 750ms;

@keyframes pulse {
  50% {
    transform: scale(1.1, 1.1);
  }
  100% {
    transform: scale(1, 1);
  }
}

@keyframes greydientTo {
  to {
    stop-color: rgba(229, 229, 229);
  }
}

@keyframes greydientFrom {
  from {
    stop-color: rgba(229, 229, 229);
  }
}

.component.portrait {
  transform-box: fill-box;
  transform-origin: center center;

  transition:
    opacity 1500ms ease,
    transform 750ms ease;
  will-change: transform, opacity;
  opacity: 1;

  .fill,
  .text {
    transition:
      fill $ttime ease,
      stroke $ttime ease;

    will-change: fill, stroke;
  }

  &.hidden {
    opacity: 0;
  }

  &.highlighted {
    animation: pulse 750ms ease-out;
  }

  &.active .fill-gradient stop {
    animation: greydientFrom 750ms ease forwards;
  }

  &:not(.active) {
    .fill[fill]:not([fill="white"]) {
      fill: rgba(229, 229, 229);
    }

    .fill[stroke]:not([stroke="white"]) {
      stroke: rgb(229, 229, 229);
    }

    .fill-gradient stop {
      animation: greydientTo 750ms ease forwards;
    }

    .text[fill] {
      fill: #756b61;
    }
  }
}
</style>
