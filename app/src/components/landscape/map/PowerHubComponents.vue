<template>
  <g id="power-hub-components">
    <TheSun
      x="151"
      y="428"
    />
    <HeatTubes
      :power-hub="powerHub"
      x="367"
      y="508"
    />
    <HeatStorage
      :power-hub="powerHub"
      x="549"
      y="508"
    />
    <AbsorptionChiller
      :power-hub="powerHub"
      x="761"
      y="591"
    />
    <CompressionChiller
      :power-hub="powerHub"
      x="759"
      y="452"
    />
    <CoolingDemand
      :power-hub="powerHub"
      x="1067"
      y="521"
    />
    <SolarPanels
      :power-hub="powerHub"
      x="366"
      y="368"
    />
    <PowerBattery
      :power-hub="powerHub"
      x="557"
      y="364"
    />
    <SystemDemand
      :power-hub="powerHub"
      x="941"
      y="368"
    />
    <SeaWater
      x="152"
      y="634"
    />
    <WaterMaker
      :power-hub="powerHub"
      x="365"
      y="643"
    />
    <WaterStorage
      :power-hub="powerHub"
      x="557"
      y="701"
    />
    <WaterTreatment
      :power-hub="powerHub"
      x="756"
      y="795"
    />
    <WaterDemand
      :power-hub="powerHub"
      x="952"
      y="706"
    />
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
import AbsorptionChiller from "./AbsorptionChiller.vue";
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
