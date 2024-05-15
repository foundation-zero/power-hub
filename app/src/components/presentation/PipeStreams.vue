<template>
  <g
    id="pipe-streams"
    ref="streams"
  >
    <path
      :class="journeys.water.streams[0]"
      d="M281 697 H364"
      stroke="#4A8AD2"
      stroke-width="4"
    />
    <path
      :class="journeys.water.streams[1]"
      d="M478 698L558 740.5"
      stroke="#4A8AD2"
      stroke-width="4"
    />

    <path
      :class="journeys.water.streams[2]"
      d="M 669 766.5 H952"
      stroke="#4A8AD2"
      stroke-width="4"
    />

    <path
      :class="journeys.water.streams[3]"
      d="M960 788.5L868.5 832.5"
      stroke="#4A8AD2"
      stroke-width="4"
    />

    <path
      :class="journeys.water.streams[4]"
      d="M 756.5 831.5 L 659.5 788.5"
      stroke="#4A8AD2"
      stroke-width="4"
    />

    <path
      :class="{ flowing: journeys.water.streams[2].flowing }"
      data-flow
      d="M 669 766.5 H952"
      stroke="#4A8AD2"
      stroke-width="4"
    />

    <path
      :class="{ flowing: journeys.water.streams[3].flowing }"
      data-flow
      d="M960 788.5L868.5 832.5"
      stroke="#4A8AD2"
      stroke-width="4"
    />

    <path
      :class="{ flowing: journeys.water.streams[4].flowing }"
      data-flow
      d="M 756.5 831.5 L 659.5 788.5"
      stroke="#4A8AD2"
      stroke-width="4"
    />

    <path
      d="M600 423.5L775 499.5"
      stroke="white"
      stroke-width="4"
    />
    <path
      :class="journeys.electrical.streams[0]"
      d="M 280 494 H319 L 376.5 458.5"
      stroke="#EAD17E"
      stroke-width="4"
    />
    <path
      :class="journeys.electrical.streams[1]"
      d="M 478 423 H 557"
      stroke="#F9E297"
      stroke-width="4"
    />
    <path
      :class="journeys.electrical.streams[2]"
      d="M 668 423 H 940"
      stroke="#F9E297"
      stroke-width="4"
    />

    <path
      :class="journeys.heat.streams[0]"
      d="M 280 494 H 319 L 375 529.5"
      stroke="#EAD17E"
      stroke-width="4"
    />

    <path
      :class="journeys.heat.streams[1]"
      d="M480 562L521 562L557 562"
      stroke="#DCACB0"
      stroke-width="4"
    />

    <path
      :class="journeys.heat.streams[2]"
      d="M664.5 585.5L764 629.5"
      stroke="#DCACB0"
      stroke-width="4"
    />

    <path
      :class="journeys.heat.streams[4]"
      d="M 863 536 L 965 581.5 L1067 580"
      stroke="#DCACB0"
      stroke-width="4"
    />

    <path
      :class="journeys.heat.streams[4]"
      d="M 869 628.5 L 965 581.5 L1067 580"
      stroke="#DCACB0"
      stroke-width="4"
    />

    <path
      d="M318.354 494.446L329 501"
      stroke="url(#paint2_linear_481_1151)"
      stroke-width="4"
    />
    <defs>
      <linearGradient
        id="paint0_linear_481_1151"
        x1="320.989"
        y1="494.446"
        x2="423.718"
        y2="560.446"
        gradientUnits="userSpaceOnUse"
      >
        <stop stop-color="#E9D17E" />
        <stop
          offset="1"
          stop-color="#DCACB0"
        />
      </linearGradient>
      <linearGradient
        id="paint1_linear_481_1151"
        x1="423.66"
        y1="428.009"
        x2="321.012"
        y2="495.009"
        gradientUnits="userSpaceOnUse"
      >
        <stop stop-color="#F9E297" />
        <stop
          offset="1"
          stop-color="#E9D17E"
        />
      </linearGradient>
      <linearGradient
        id="paint2_linear_481_1151"
        x1="320.989"
        y1="494.446"
        x2="423.718"
        y2="560.446"
        gradientUnits="userSpaceOnUse"
      >
        <stop stop-color="#E9D17E" />
        <stop
          offset="1"
          stop-color="#DCACB0"
        />
      </linearGradient>
    </defs>
  </g>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@/stores/presentation";
import { onMounted } from "vue";
import { ref } from "vue";

const streams = ref<SVGElement>();

const { journeys } = usePresentationStore();

onMounted(() => {
  streams.value?.querySelectorAll<SVGGeometryElement>("path:not([data-flow])").forEach((el) => {
    el.style.strokeDasharray = el.getTotalLength() + "";
    el.style.strokeDashoffset = el.getTotalLength() + "";
  });
});
</script>

<style lang="scss" scoped>
$ttime: 750ms;

@keyframes snake {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes stream {
  from {
    stroke-dashoffset: 100;
  }

  to {
    stroke-dashoffset: 0;
  }
}

path {
  will-change: stroke-dashoffset, opacity;
  transition: opacity $ttime ease;
  opacity: 0;

  &.active {
    opacity: 1;
    animation: snake 500ms linear forwards;
  }

  &.muted {
    opacity: 0;
  }

  &[data-flow] {
    stroke-dasharray: 5;
    stroke: white;

    &.flowing {
      opacity: 0.6;
      animation: stream 2500ms linear infinite;
    }
  }
}
</style>
