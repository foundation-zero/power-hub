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
      font-size="38"
      letter-spacing="0em"
    >
      <tspan
        x="397"
        y="721.04"
      >
        From the battery &#10;
      </tspan>
      <tspan
        x="397"
        y="765.04"
      >
        we feed heat into the&#10;
      </tspan>
      <tspan
        x="397"
        y="809.04"
      >
        absorption chiller....
      </tspan>
    </text>
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "FromTheBattery",
  components: { AnimatedSlide },
};
</script>
