<template>
  <AnimatedSlide
    fade
    delay
  >
    <text
      fill="black"
      xml:space="preserve"
      style="white-space: pre"
      font-family="Five Gothic"
      font-size="40"
      letter-spacing="0em"
    >
      <tspan
        x="396"
        y="736.7"
      >
        Harvesting thermal&#10;
      </tspan>
      <tspan
        x="396"
        y="782.7"
      >
        energy from sunlight using &#10;
      </tspan>
      <tspan
        x="396"
        y="828.7"
      >
        heat tubes
      </tspan>
    </text>
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "HarvestingThermalEnergy",
  components: { AnimatedSlide },
};
</script>
