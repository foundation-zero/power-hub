<template>
  <AnimatedSlide fade>
    <text
      fill="#D4D4D4"
      xml:space="preserve"
      style="white-space: pre"
      font-family="Five-Gothic"
      font-size="270"
      font-weight="bold"
      letter-spacing="0em"
      transform="translate(938, 146)"
      ><tspan
        x="-7"
        y="187.1"
        >3x</tspan
      ></text
    >
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "ThreeTimes",
  components: { AnimatedSlide },
};
</script>

<style scoped lang="scss">
div {
  will-change: transform;
  transition: transform 750ms ease;

  &.slide-leave-to,
  &.slide-enter-from {
    transform: scale(2, 2);
  }
}
</style>
