<template>
  <AnimatedSlide
    class="gauge"
    fade
  >
    <BatteryGauge />
  </AnimatedSlide>
</template>

<script lang="ts">
import BatteryGauge from "../../gauges/BatteryGauge.vue";
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "HeatPipesGaugeAnimated",
  components: { AnimatedSlide, BatteryGauge },
};
</script>

<style scoped lang="scss">
.gauge {
  will-change: transform, opacity;
  transition:
    transform 750ms,
    opacity 750ms ease;
  transform: translate(1250px, 700px);
}

.slide-leave-to,
.slide-enter-from {
  transform: translate(1920px, 700px);
}
</style>
