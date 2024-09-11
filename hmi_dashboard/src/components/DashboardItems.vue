<script setup lang="ts">
import CompoundPanel from "@/components/CompoundPanel.vue";
import CoolingPanel from "@/components/CoolingPanel.vue";
import WaterPanel from "@/components/WaterPanel.vue";
import { usePowerHubStore } from "@/stores/power-hub";
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
