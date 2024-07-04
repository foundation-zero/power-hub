<template>
  <AnimatedSlide fade>
    <rect
      x="356"
      y="583"
      width="23"
      height="65"
      transform="rotate(90 356 583)"
      fill="#E6E6E6"
    />
    <rect
      x="311"
      y="562"
      width="22"
      height="65"
      fill="#E6E6E6"
    />

    <line
      x1="1018"
      y1="110"
      x2="1018"
      y2="226"
      stroke="#A7A7A7"
      stroke-width="1"
    />
    <text
      fill="black"
      xml:space="preserve"
      style="white-space: pre"
      font-size="50"
      letter-spacing="0em"
      ><tspan
        x="1068"
        y="160"
        >Electrical energy</tspan
      ></text
    >
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "BaseElectrical",
  components: { AnimatedSlide },
};
</script>
