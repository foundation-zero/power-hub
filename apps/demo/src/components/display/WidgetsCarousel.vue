<template>
  <section
    class="sensor-widgets pa-3 ma-n3"
    :class="{ inactive: !presentation.showWidgets }"
  >
    <v-row>
      <v-col cols="12">
        <ProductionChartWidget />
      </v-col>
      <v-col cols="12">
        <CoolingDemandWidget :power-hub="powerhub" />
      </v-col>
      <v-col cols="12">
        <WaterDemandWidget :power-hub="powerhub" />
      </v-col>
    </v-row>
  </section>
</template>

<script setup lang="ts">
import { usePowerHubStore } from "@shared/stores/power-hub";
import ProductionChartWidget from "../widgets/ProductionChartWidget.vue";
import CoolingDemandWidget from "../widgets/CoolingDemandWidget.vue";
import WaterDemandWidget from "../widgets/WaterDemandWidget.vue";
import { usePresentationStore } from "@demo/stores/presentation";

const presentation = usePresentationStore();

const store = usePowerHubStore();
const powerhub = await store.connect();
</script>

<style lang="scss" scoped>
.sensor-widgets {
  position: absolute;
  width: 375px;
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
