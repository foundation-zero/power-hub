<template>
  <AnimatedSlide fade>
    <text
      fill="black"
      xml:space="preserve"
      style="white-space: pre"
      font-size="30"
      letter-spacing="0em"
    >
      <tspan
        x="950"
        y="190.9"
      >
        Welcome to the Power Hub,&#10;
      </tspan>
      <tspan
        x="950"
        y="224.9"
      >
        this display takes you through&#10;
      </tspan>
      <tspan
        x="950"
        y="258.9"
      >
        the technology of the &#10;
      </tspan>
      <tspan
        x="950"
        y="292.9"
      >
        power hub
      </tspan>
    </text>
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "./AnimatedSlide.vue";

export default {
  name: "WelcomeToThePowerHub",
  components: { AnimatedSlide },
};
</script>
