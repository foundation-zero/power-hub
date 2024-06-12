<template>
  <AnimatedSlide
    class="gauge"
    fade
  >
    <CompoundTemperatureGague />
  </AnimatedSlide>
</template>

<script lang="ts">
import CompoundTemperatureGague from "../../gauges/CompoundTemperatureGauge.vue";
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "CompoundTemperatureAnimated",
  components: { AnimatedSlide, CompoundTemperatureGague },
};
</script>

<style scoped lang="scss">
.gauge {
  will-change: transform, opacity;
  transition:
    transform 750ms,
    opacity 750ms ease;
  transform: translate(1350px, 700px);
}

.slide-leave-to,
.slide-enter-from {
  transform: translate(1920px, 700px);
}
</style>
