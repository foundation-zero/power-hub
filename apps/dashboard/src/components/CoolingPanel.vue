<template>
  <v-card class="pa-8 mt-8">
    <h3 class="text-h4 font-weight-thin d-flex align-center">
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
          :min="0"
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
          :min="0"
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
          name="Chilled"
          :value="useValue('rh33Chill')"
          :history="useLast24Hours('rh33Chill/deltaTemperature')"
          :flow="useValue('chilledFlowSensor/flow')"
        />
      </v-col>
    </v-row>
  </v-card>
  <v-card class="pa-8 mt-8">
    <h3 class="text-h4 font-weight-thin d-flex align-center">
      <v-icon
        size="24"
        icon="fa-temperature-low"
        class="mr-5"
      />
      Cooling demand
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
          name="Cooling demand"
          :value="useValue('coldReservoir/coolingDemand')"
          :history="useLast24Hours('coldReservoir/coolingDemand')"
          :min="0"
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
          name="Cooling demand"
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
        <TemperatureBlock
          name="Cold reservoir"
          :value="useValue('coldReservoir/temperature')"
          :history="useLast24Hours('coldReservoir/temperature')"
        />
      </v-col>
    </v-row>
  </v-card>
  <v-card class="pa-8 mt-8">
    <h3 class="text-h4 font-weight-thin d-flex align-center">
      <v-icon
        size="24"
        icon="fa-fire-flame-simple"
        class="mr-5"
      />
      PCM
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
          name="PCM"
          :value="useValue('pcm/netCharge')"
          :history="useLast24Hours('pcm/netCharge')"
          :power-in="useValue('pcm/chargePower')"
          :power-out="useValue('pcm/dischargePower')"
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
        <TemperatureBlock
          name="PCM"
          :value="useValue('pcm/temperature')"
          :history="useLast24Hours('pcm/temperature')"
        />
      </v-col>
    </v-row>
  </v-card>
  <v-card class="pa-8 mt-8">
    <h3 class="text-h4 font-weight-thin d-flex align-center">
      <v-icon
        size="24"
        icon="fa-water"
        class="mr-5"
      />
      Waste
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
          name="Heat dump"
          :value="useValue('outboardExchange/power')"
          :history="useLast24Hours('outboardExchange/power')"
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
    </v-row>
  </v-card>
</template>

<script setup lang="ts">
import { type PowerHubStore } from "@shared/stores/power-hub";
import TemperatureBlock from "./TemperatureBlock.vue";
import { toActiveState, toChargeState, useSensorValue, useLast24Hours } from "@shared/utils";
import CircuitBlock from "./CircuitBlock.vue";
import { useObservable } from "@vueuse/rxjs";
import { map } from "rxjs";
import CoolingBlock from "./CoolingBlock.vue";

const { powerHub } = defineProps<{ powerHub: PowerHubStore }>();
const useValue = useSensorValue(powerHub);

const yazakiState = useObservable(
  powerHub.controlValues.useMqtt("yazaki/on").pipe(map(toActiveState)),
);

const chillerState = useObservable(
  powerHub.controlValues.useMqtt("chiller/on").pipe(map(toActiveState)),
);

const pcmState = useObservable(useValue("pcm/netCharge").pipe(map(toChargeState)));
</script>
