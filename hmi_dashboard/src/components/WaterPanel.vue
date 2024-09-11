<template>
  <v-card class="pa-8">
    <h3 class="text-h4 font-weight-thin mb-8 d-flex align-center">
      <v-icon
        size="24"
        icon="fa-droplet"
        class="mr-5"
      />
      Water
    </h3>

    <v-row>
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <WaterBlock
          name="Fresh water"
          color="blue-lighten-1"
          :value="useValue('freshWaterTank/fillRatio')"
          :history="useLast24Hours('freshWaterTank/fillRatio')"
          :max="waterTankCapacity.freshWater"
          :status="freshWaterStatus"
          :thresholds="waterTankThresholds.freshWater"
        />
      </v-col>
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <WaterBlock
          color="white"
          name="Grey water"
          :value="useValue('greyWaterTank/fillRatio')"
          :history="useLast24Hours('greyWaterTank/fillRatio')"
          :max="waterTankCapacity.greyWater"
          :thresholds="waterTankThresholds.greyWater"
        />
      </v-col>
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
        ><WaterBlock
          color="cyan"
          name="Technical water"
          :value="useValue('technicalWaterTank/fillRatio')"
          :history="useLast24Hours('technicalWaterTank/fillRatio')"
          :status="technicalWaterStatus"
          :thresholds="waterTankThresholds.technicalWater"
          :max="waterTankCapacity.technicalWater"
        />
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
        ><WaterBlock
          name="Black water"
          color="grey-lighten-3"
          :value="useValue('blackWaterTank/fillRatio')"
          :history="useLast24Hours('blackWaterTank/fillRatio')"
          :thresholds="waterTankThresholds.blackWater"
          :max="waterTankCapacity.blackWater"
        />
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup lang="ts">
import WaterBlock from "./WaterBlock.vue";
import { useObservable } from "@vueuse/rxjs";
import type { PowerHubStore } from "@/stores/power-hub";
import { map } from "rxjs";
import { waterTankCapacity, waterTankThresholds } from "@/utils/const";
import { useLast24Hours, useSensorValue } from "@/utils";

const { powerHub } = defineProps<{ powerHub: PowerHubStore }>();
const useValue = useSensorValue(powerHub);

const freshWaterStatus = useObservable(
  powerHub.controlValues
    .useMqtt("waterFilterBypassValve")
    .pipe(map((valve) => (valve.position === 1 ? "Idle" : "Filtering"))),
);
const technicalWaterStatus = useObservable(
  useValue("freshWaterTank/flowToTechnical").pipe(
    map((val) => (val > 0 ? "Filling from fresh" : "Idle")),
  ),
);
</script>
