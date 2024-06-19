<template>
  <AnimatedSlide
    class="gauge"
    fade
  >
    <BatteryGauge
      width="498"
      height="260"
    />
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
  transform: translate(65%, 65%);
}

.slide-leave-to,
.slide-enter-from {
  transform: translate(100%, 65%);
}
</style>
