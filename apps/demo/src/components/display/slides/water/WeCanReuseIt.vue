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
        x="409"
        y="474.2"
        >The Power Hub is able to reuse </tspan
      ><tspan
        x="409"
        y="520.2"
        >water up to three times for </tspan
      ><tspan
        x="409"
        y="566.2"
        >different purposes.</tspan
      ></text
    >
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "WeCanReuseIt",
  components: { AnimatedSlide },
};
</script>
