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
        y="451.2"
        >Wastewater without harsh </tspan
      ><tspan
        x="409"
        y="497.2"
        >chemicals is used for flushing&#10;</tspan
      ><tspan
        x="409"
        y="543.2"
        >the toilet and washing down &#10;</tspan
      ><tspan
        x="409"
        y="589.2"
        >the boat.</tspan
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
