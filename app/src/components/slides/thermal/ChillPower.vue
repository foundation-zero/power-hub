<template>
  <AnimatedSlide
    class="gauge"
    fade
  >
    <ChillPowerGauge />
  </AnimatedSlide>
</template>

<script lang="ts">
import ChillPowerGauge from "../../gauges/ChillPowerGauge.vue";
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "HeatPipesGaugeAnimated",
  components: { AnimatedSlide, ChillPowerGauge },
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
