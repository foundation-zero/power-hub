<template>
  <section
    class="sensor-widgets pa-3 ma-n3"
    :class="{ inactive: !presentation.showWidgets }"
  >
    <SensorWidgets>
      <ProductionChartWidget />
    </SensorWidgets>
  </section>
</template>

<script setup lang="ts">
import { usePowerHubStore } from "@/stores/power-hub";
import SensorWidgets from "@/components/SensorWidgets.vue";

import ProductionChartWidget from "./widgets/ProductionChartWidget.vue";
import { usePresentationStore } from "@/stores/presentation";

const presentation = usePresentationStore();

const store = usePowerHubStore();
await store.connect();
</script>

<style lang="scss" scoped>
.sensor-widgets {
  position: absolute;
  width: 450px;
  top: 50%;
  transform: translate(0, -50%);
  transition:
    transform 500ms ease,
    opacity 500ms ease;
  opacity: 1;
  right: 50px;
  will-change: transform, opacity;

  &.inactive {
    opacity: 0;
    transform: translate(calc(100% + 50px), -50%);
  }
}
</style>
