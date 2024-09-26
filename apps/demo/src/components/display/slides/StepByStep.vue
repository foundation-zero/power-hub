<template>
  <AnimatedSlide
    fade
    delay
  >
    <text
      fill="black"
      xml:space="preserve"
      style="white-space: pre"
      font-size="30"
      letter-spacing="0em"
      ><tspan
        x="1004"
        y="186.9"
        >We will explain step-by-step &#10;</tspan
      ><tspan
        x="1004"
        y="220.9"
        >what happens inside the container, </tspan
      ><tspan
        x="1004"
        y="254.9"
        >and how it generates and provides </tspan
      ><tspan
        x="1004"
        y="288.9"
        >renewable energy.</tspan
      ></text
    >
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "./AnimatedSlide.vue";

export default {
  name: "StepByStep",
  components: { AnimatedSlide },
};
</script>
