<template>
  <v-card class="pa-8">
    <h3 class="text-h4 font-weight-thin mb-8 d-flex align-center">
      <v-icon
        size="24"
        icon="fa-snowflake"
        class="mr-5"
      />
      Cooling
    </h3>

    <v-row class="mt-3">
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <CoolingBlock
          name="Chiller"
          :value="useValue('chiller/chillPower')"
          :history="useLast24Hours('chiller/chillPower')"
          :status="chillerState"
        />
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <CoolingBlock
          name="Yazaki"
          :value="useValue('yazaki/chillPower')"
          :history="useLast24Hours('yazaki/chillPower')"
          :status="yazakiState"
        />
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <CoolingBlock
          name="Cooling demand"
          :value="useValue('coldReservoir/coolingSupply')"
          :history="useLast24Hours('coldReservoir/coolingSupply')"
        />
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <CoolingBlock
          name="PCM"
          :value="useValue('pcm/netCharge')"
          :history="useLast24Hours('pcm/netCharge')"
          :status="pcmState"
        />
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <CoolingBlock
          name="Heat dump"
          :value="useValue('outboardExchange/power')"
          :history="useLast24Hours('outboardExchange/power')"
        />
      </v-col>
    </v-row>
    <v-row>
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <CircuitBlock
          name="Chilled"
          :value="useValue('rh33Chill')"
          :history="useLast24Hours('rh33Chill/deltaTemperature')"
          :flow="useValue('chilledFlowSensor/flow')"
        />
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <CircuitBlock
          name="Hot supply"
          :value="useValue('rh33YazakiHot')"
          :history="useLast24Hours('rh33YazakiHot/deltaTemperature')"
          :flow="useValue('yazakiHotFlowSensor/flow')"
        />
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <CircuitBlock
          name="Cooling supply"
          :value="useValue('rh33CoolingDemand')"
          :history="useLast24Hours('rh33CoolingDemand/deltaTemperature')"
          :flow="useValue('coolingDemandFlowSensor/flow')"
        />
      </v-col>

      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <CircuitBlock
          name="Waste"
          :value="useValue('rh33Waste')"
          :history="useLast24Hours('rh33Waste/deltaTemperature')"
          :flow="useValue('wasteFlowSensor/flow')"
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <TemperatureBlock
          name="Waste (harbour)"
          :value="useValue('outboardTemperatureSensor/temperature')"
          :history="useLast24Hours('outboardTemperatureSensor/temperature')"
        />
      </v-col>
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <TemperatureBlock
          name="Cold reservoir"
          :value="useValue('coldReservoir/temperature')"
          :history="useLast24Hours('coldReservoir/temperature')"
        />
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup lang="ts">
import { type PowerHubStore } from "@/stores/power-hub";
import TemperatureBlock from "./TemperatureBlock.vue";
import { useActiveState, useChargeState, useSensorValue, useLast24Hours } from "@/utils";
import CircuitBlock from "./CircuitBlock.vue";
import { useObservable } from "@vueuse/rxjs";
import { map } from "rxjs";
import CoolingBlock from "./CoolingBlock.vue";

const { powerHub } = defineProps<{ powerHub: PowerHubStore }>();
const useValue = useSensorValue(powerHub);

const yazakiState = useObservable(
  powerHub.controlValues.useMqtt("yazaki/on").pipe(map(useActiveState)),
);

const chillerState = useObservable(
  powerHub.controlValues.useMqtt("chiller/on").pipe(map(useActiveState)),
);

const pcmState = useObservable(useValue("pcm/netCharge").pipe(map(useChargeState)));
</script>
