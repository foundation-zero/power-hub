<template>
  <g
    :id="component"
    ref="el"
    class="component"
    :class="{ ...state, [mode]: true }"
    @mouseenter="onHover"
    @mouseleave="onLeave"
    @touchstart="onTouch"
    @click="onClick"
    @touchend="onLeave"
  >
    >
    <svg
      :height="height"
      :width="width"
      v-bind="$attrs"
      :viewBox="viewBox"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <slot />
    </svg>
  </g>
</template>

<script lang="ts">
// use normal <script> to declare options
export default {
  inheritAttrs: true,
};
</script>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { usePresentationStore } from "@/stores/presentation";
import type { PowerHubComponent } from "@/types/power-hub";
import type { Journey } from "@/types";
import { activate, deactivate, dehighlight, hide, highlight, show } from "@/utils";
import { toRefs } from "vue";
import { useRouter } from "vue-router";

const { component, journey } = defineProps<{
  component: PowerHubComponent;
  width: string;
  height: string;
  viewBox: string;
  journey: Journey;
}>();

const el = ref<SVGElement>();
const router = useRouter();
const { getComponentState, componentStates, streamStates, getFlow } = usePresentationStore();
const { root, mode, currentJourney } = toRefs(usePresentationStore());

const state = computed(() => getComponentState(component));
const touched = ref(false);

onMounted(() => {
  if (!el.value) return;

  const svg = root.value!.getBoundingClientRect();
  const viewBox = root.value!.viewBox;

  const dx = viewBox.baseVal.width / svg!.width;
  const dy = viewBox.baseVal.height / svg!.height;
  const dimensions = el.value!.getBoundingClientRect();

  const x = dimensions.left + dimensions.width / 2;
  const y = dimensions.top + dimensions.height / 2;
  el.value.style.transformOrigin = `${(x - svg.left) * dx}px ${(y - svg.top) * dy}px`;
});

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
    if (mode.value !== "display") {
      router.push(`/journeys/${journey}`);
    }

    touched.value = false;
  }, 500);
};

const onClick = () => {
  if (touched.value) return;

  if (mode.value !== "display") {
    router.push(`/journeys/${journey}`);
  }
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

@keyframes pulseBig {
  50% {
    transform: scale(1.25, 1.25);
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

.component {
  &.display {
    &.highlighted {
      animation: pulseBig 750ms ease-out;
    }
  }

  &.landscape {
    &.highlighted {
      animation: pulse 750ms ease-out;
    }
  }

  &.landscape,
  &.display {
    transition:
      opacity 1500ms ease,
      transform 750ms ease;
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

    &.hidden {
      opacity: 0;
    }

    &.active .fill-gradient stop {
      animation: greydientFrom 750ms ease forwards;
    }

    &:not(.active) {
      .fill[fill]:not([fill="white"]) {
        fill: rgba(229, 229, 229);
      }

      .fill-gradient stop {
        animation: greydientTo 750ms ease forwards;
      }

      .fill[stroke]:not([stroke="white"]) {
        stroke: rgb(229, 229, 229);
      }

      .text[fill] {
        fill: #756b61;
      }
    }
  }
}
</style>
