<template>
  <AnimatedSlide
    class="gauge"
    fade
  >
    <ChillPowerGauge />
  </AnimatedSlide>
</template>

<script lang="ts">
import ChillPowerGauge from "../../../gauges/ChillPowerGauge.vue";
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "ChillPowerGaugeAnimated",
  components: { AnimatedSlide, ChillPowerGauge },
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
