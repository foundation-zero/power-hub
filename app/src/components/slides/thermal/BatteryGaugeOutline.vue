<template>
  <AnimatedSlide
    class="gauge"
    fade
  >
    <path
      transform="translate(-98, -23)"
      d="M1690 825H1798.62L1826 849.5L1798.62 874H1690"
      stroke="#D4999D"
      stroke-width="2"
    />
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "BatteryGaugeOutline",
  components: { AnimatedSlide },
};
</script>
