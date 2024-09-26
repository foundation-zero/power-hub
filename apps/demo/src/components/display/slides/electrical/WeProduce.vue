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
        x="403"
        y="589.7"
        >The Power Hub produces </tspan
      ><tspan
        x="403"
        y="635.7"
        >up to 40 kW of electrical </tspan
      ><tspan
        x="403"
        y="681.7"
        >power &#x2014; depending on </tspan
      ><tspan
        x="403"
        y="727.7"
        >the available sunlight.</tspan
      ></text
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
