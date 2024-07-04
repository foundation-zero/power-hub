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
    >
      <tspan
        x="403"
        y="589.7"
      >
        The electricity the Power
      </tspan>
      <tspan
        x="403"
        y="635.7"
      >
        Hub produces can be
      </tspan>
      <tspan
        x="403"
        y="681.7"
      >
        stored in its battery for
      </tspan>
      <tspan
        x="403"
        y="727.7"
      >
        later use.
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
