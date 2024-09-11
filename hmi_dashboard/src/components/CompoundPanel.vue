<script setup lang="ts">
import { type PowerHubStore } from "@/stores/power-hub";
import TemperatureBlock from "./TemperatureBlock.vue";
import { useSensorValue, useLast24Hours } from "@/utils";

const { powerHub } = defineProps<{ powerHub: PowerHubStore }>();

const useValue = useSensorValue(powerHub);
</script>

<template>
  <v-card class="pa-8">
    <h3 class="text-h4 font-weight-thin mb-8 d-flex align-center">
      <v-icon
        size="24"
        icon="fa-tent"
        class="mr-5"
      />
      Compound
    </h3>
    <v-row class="mt-3">
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <TemperatureBlock
          name="Powerhub"
          :value="useValue('powerHubFancoil/ambientTemperature')"
          :set-point="useValue('powerHubFancoil/setpoint')"
          :history="useLast24Hours('powerHubFancoil/ambientTemperature')"
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
          name="Sanitary"
          :value="useValue('sanitaryFancoil/ambientTemperature')"
          :set-point="useValue('sanitaryFancoil/setpoint')"
          :history="useLast24Hours('sanitaryFancoil/ambientTemperature')"
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
          name="Kitchen"
          :value="useValue('kitchenFancoil/ambientTemperature')"
          :set-point="useValue('kitchenFancoil/setpoint')"
          :history="useLast24Hours('kitchenFancoil/ambientTemperature')"
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
          name="Office #1"
          :value="useValue('office1Fancoil/ambientTemperature')"
          :set-point="useValue('office1Fancoil/setpoint')"
          :history="useLast24Hours('office1Fancoil/ambientTemperature')"
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
          name="Office #2"
          :value="useValue('office2Fancoil/ambientTemperature')"
          :set-point="useValue('office2Fancoil/setpoint')"
          :history="useLast24Hours('office2Fancoil/ambientTemperature')"
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
          name="Simulator"
          :value="useValue('simulatorFancoil/ambientTemperature')"
          :set-point="useValue('simulatorFancoil/setpoint')"
          :history="useLast24Hours('simulatorFancoil/ambientTemperature')"
        />
      </v-col>
    </v-row>
  </v-card>
</template>
