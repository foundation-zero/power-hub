<template>
  <g id="power-hub-components">
    <TheSun />
    <HeatTubes :power-hub="powerHub" />
    <HeatStorage :power-hub="powerHub" />
    <AbsorbtionChiller :power-hub="powerHub" />
    <CompressionChiller :power-hub="powerHub" />
    <CoolingDemand :power-hub="powerHub" />
    <SolarPanels :power-hub="powerHub" />
    <PowerBattery :power-hub="powerHub" />
    <SystemDemand :power-hub="powerHub" />
    <SeaWater />
    <WaterMaker :power-hub="powerHub" />
    <WaterStorage :power-hub="powerHub" />
    <WaterTreatment :power-hub="powerHub" />
    <WaterDemand :power-hub="powerHub" />
    <defs>
      <clipPath id="clip0_481_1610">
        <rect
          width="1481"
          height="1080"
          fill="white"
        />
      </clipPath>
      <clipPath id="clip1_481_1610">
        <rect
          width="35"
          height="45"
          fill="white"
          transform="translate(200 659)"
        />
      </clipPath>
      <clipPath id="clip2_481_1610">
        <rect
          width="26.6371"
          height="26.6371"
          fill="white"
          transform="translate(994 730)"
        />
      </clipPath>
      <clipPath id="clip3_481_1610">
        <rect
          x="404.649"
          y="385"
          width="31"
          height="31"
          rx="15.5"
          fill="white"
        />
      </clipPath>
    </defs>
  </g>
</template>

<script setup lang="ts">
import TheSun from "./TheSun.vue";
import SolarPanels from "./SolarPanels.vue";
import HeatTubes from "./HeatTubes.vue";
import HeatStorage from "./HeatStorage.vue";
import AbsorbtionChiller from "./AbsorptionChiller.vue";
import CompressionChiller from "./CompressionChiller.vue";
import CoolingDemand from "./CoolingDemand.vue";
import PowerBattery from "./PowerBattery.vue";
import SystemDemand from "./SystemDemand.vue";
import SeaWater from "./SeaWater.vue";
import WaterMaker from "./WaterMaker.vue";
import WaterStorage from "./WaterStorage.vue";
import WaterTreatment from "./WaterTreatment.vue";
import WaterDemand from "./WaterDemand.vue";

import { usePowerHubStore } from "@/stores/power-hub";

const store = usePowerHubStore();
const powerHub = await store.connect();
</script>
