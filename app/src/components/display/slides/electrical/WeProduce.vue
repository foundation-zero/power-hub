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
      transform="translate(413, 534)"
      ><tspan
        x="0"
        y="27.7"
        >We produce up to 40 kW &#10;</tspan
      ><tspan
        x="0"
        y="73.7"
        >per hour depending on &#10;</tspan
      ><tspan
        x="0"
        y="119.7"
        >the sun light....
      </tspan></text
    >
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "WeProduce",
  components: { AnimatedSlide },
};
</script>
