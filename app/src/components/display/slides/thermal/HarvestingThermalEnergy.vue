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
      ><tspan
        x="396"
        y="759.7"
        >The Power Hub uses heat pipes to </tspan
      ><tspan
        x="396"
        y="805.7"
        >harvest energy from sunlight.</tspan
      ></text
    >
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "HarvestingThermalEnergy",
  components: { AnimatedSlide },
};
</script>
