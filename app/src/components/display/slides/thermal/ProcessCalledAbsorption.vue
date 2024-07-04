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
    >
      <tspan
        x="1009"
        y="210.9"
      >
        It does this by harvesting &#10;
      </tspan>
      <tspan
        x="1009"
        y="244.9"
      >
        heat through a process &#10;
      </tspan>
      <tspan
        x="1009"
        y="278.9"
      >
        called &#x2018;absorption.&#x2019;
      </tspan>
    </text>
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "ThemeIcon",
  components: { AnimatedSlide },
};
</script>
