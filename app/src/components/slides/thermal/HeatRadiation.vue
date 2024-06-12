<template>
  <AnimatedSlide fade>
    <circle
      cx="424"
      cy="566"
      r="128"
      stroke="#D4999D"
      stroke-width="8"
    />

    <circle
      cx="424"
      cy="566"
      r="168.5"
      stroke="#E1E1E1"
      stroke-width="3"
    />
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "HeatRadiation",
  components: { AnimatedSlide },
};
</script>

<style scoped lang="scss">
circle,
circle {
  will-change: r;
  transition: r 3000ms ease;
}

.slide-leave-to circle,
.slide-enter-from circle {
  r: 62;
}
</style>
