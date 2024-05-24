<template>
  <AnimatedSlide fade>
    <text
      fill="black"
      xml:space="preserve"
      style="white-space: pre"
      font-family="Five-Gothic"
      font-size="40"
      letter-spacing="0em"
      transform="translate(410, 500)"
    >
      <tspan
        x="-1"
        y="28.2"
      >
        Reusing water is more
      </tspan>
      <tspan
        x="-1"
        y="74.2"
      >
        efficient than making new
      </tspan>
    </text>
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "ReusingWater",
  components: { AnimatedSlide },
};
</script>
