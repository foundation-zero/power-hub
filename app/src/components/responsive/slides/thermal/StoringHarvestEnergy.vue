<template>
  <TextSlide journey="heat">
    <template #title>Storing harvested energy in the heat battery</template>
    <template #body>
      <HeatBatteryGauge
        width="100%"
        :height="undefined"
      />
      <p>
        The heat from the heat pipes is fed through a phase change material. A material that melts
        and freezes at a desired temperature. During a phase change materials will stay at their
        phase transition temperature until entirety of the material has transitioned. This is why a
        boiling pot of water is locked at 100 °C.
      </p>

      <p>
        In our case the phase change material transitions at 78 °C. In melting it stores 240
        kilojoule per kilogram of material. In order to store the 40 kWh we require, we need to use
        600 kgs of PCM. However if we'd used a water reservoir we'd have needed about 1700 liters of
        water instead.
      </p>
    </template>
  </TextSlide>
</template>

<script setup lang="ts">
import HeatBatteryGauge from "@/components/gauges/BatteryGauge.vue";
import TextSlide from "../../TextSlide.vue";
</script>
