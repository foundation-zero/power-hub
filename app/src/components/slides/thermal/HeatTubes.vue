<template>
  <AnimatedSlide>
    <HeatTubes />
  </AnimatedSlide>
</template>

<script lang="ts">
import HeatTubes from "../../presentation/HeatTubes.vue";
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "HeatTubesAnimated",
  components: { AnimatedSlide, HeatTubes },
};
</script>

<style scoped lang="scss">
#heat-tubes {
  will-change: transform;
  transition: transform 3000ms ease;
  transform: scale(1.5, 1.5);
}

.slide-leave-to #heat-tubes {
  transition-duration: 500ms;
}
.slide-leave-to #heat-tubes,
.slide-enter-from #heat-tubes {
  transform: scale(1, 1);
}
</style>
