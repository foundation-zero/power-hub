<template>
  <AnimatedSlide
    class="gauge"
    fade
  >
    <HeatPipesGauge />
  </AnimatedSlide>
</template>

<script lang="ts">
import HeatPipesGauge from "../../../gauges/HeatPipesGauge.vue";
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "HeatPipesGaugeAnimated",
  components: { AnimatedSlide, HeatPipesGauge },
};
</script>

<style scoped lang="scss">
.gauge {
  will-change: transform, opacity;
  transition:
    transform 750ms,
    opacity 750ms ease;
  transform: translate(65%, 65%);
}

.slide-leave-to,
.slide-enter-from {
  transform: translate(100%, 65%);
}
</style>
