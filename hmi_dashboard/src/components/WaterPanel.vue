<template>
  <v-card class="pa-8">
    <h3 class="text-h4 font-weight-thin d-flex align-center">
      <v-icon
        size="24"
        icon="fa-droplet"
        class="mr-5"
      />
      Water
    </h3>

    <v-row class="mt-5">
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
          :max="WATER_TANK_CAPACITY.freshWater"
          :status="freshWaterStatus"
          :thresholds="WATER_TANK_THRESHOLDS.freshWater"
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
          :max="WATER_TANK_CAPACITY.greyWater"
          :thresholds="WATER_TANK_THRESHOLDS.greyWater"
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
          :thresholds="WATER_TANK_THRESHOLDS.technicalWater"
          :max="WATER_TANK_CAPACITY.technicalWater"
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
          :thresholds="WATER_TANK_THRESHOLDS.blackWater"
          :max="WATER_TANK_CAPACITY.blackWater"
        />
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
        ><FlowBlock
          name="Water maker"
          color="blue-lighten-1"
          :value="useValue('waterMaker/productionFlow')"
          :history="useLast24Hours('waterMaker/productionFlow')"
          :status="waterMakerStatus"
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
import { WATER_MAKER_STATUS, WATER_TANK_CAPACITY, WATER_TANK_THRESHOLDS } from "@/utils/const";
import { useLast24Hours, useSensorValue } from "@/utils";
import FlowBlock from "./FlowBlock.vue";

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
const waterMakerStatus = useObservable(
  useValue("waterMaker/status").pipe(map((val) => WATER_MAKER_STATUS[val])),
);
</script>
