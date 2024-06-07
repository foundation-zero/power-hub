<template>
  <AnimatedSlide
    fade
    delay
  >
    <text
      fill="black"
      xml:space="preserve"
      style="white-space: pre"
      font-size="40"
      letter-spacing="0em"
      transform="translate(410, 480)"
      ><tspan
        x="0"
        y="28.2"
        >Grey water is used for&#10;</tspan
      ><tspan
        x="0"
        y="74.2"
        >flushing toiled and boat&#10;</tspan
      ><tspan
        x="0"
        y="120.2"
        >wash down</tspan
      ></text
    >
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "GreyWaterIsUsed",
  components: { AnimatedSlide },
};
</script>
