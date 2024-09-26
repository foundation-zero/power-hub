<script setup lang="ts">
import CompoundPanel from "./CompoundPanel.vue";
import CoolingPanel from "./CoolingPanel.vue";
import WaterPanel from "./WaterPanel.vue";
import { usePowerHubStore } from "@shared/stores/power-hub";
import ElectricalPanel from "./ElectricalPanel.vue";
import ControlModes from "./ControlModes.vue";

const powerHub = await usePowerHubStore().connect();
</script>

<template>
  <ControlModes
    :power-hub="powerHub"
    class="mt-8"
  />
  <WaterPanel
    :power-hub="powerHub"
    class="mt-8"
  />
  <CoolingPanel
    class="mt-8"
    :power-hub="powerHub"
  />
  <CompoundPanel
    :power-hub="powerHub"
    class="mt-8"
  />
  <ElectricalPanel
    :power-hub="powerHub"
    class="mt-8"
  />
</template>
