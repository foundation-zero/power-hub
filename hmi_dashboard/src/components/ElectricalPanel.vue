<script setup lang="ts">
import { type PowerHubStore } from "@/stores/power-hub";
import PowerBlock from "./PowerBlock.vue";
import { useSensorValue, useLast24Hours } from "@/utils";
import BatteryBlock from "./BatteryBlock.vue";

const { powerHub } = defineProps<{ powerHub: PowerHubStore }>();

const useValue = useSensorValue(powerHub);
</script>

<template>
  <v-card class="pa-8">
    <h3 class="text-h4 font-weight-thin mb-8 d-flex align-center">
      <v-icon
        size="24"
        icon="fa-bolt"
        class="mr-5"
      />
      Electrical
    </h3>

    <v-row class="mt-3">
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <BatteryBlock
          name="Battery"
          :value="useValue('electrical/batterySystemSoc')"
          :history="useLast24Hours('electrical/batterySystemSoc')"
          :charge-state="useValue('electrical/vebusChargeState')"
        />
      </v-col>
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <PowerBlock
          name="PV Panels"
          :value="useValue('electrical/pvPower')"
          :history="useLast24Hours('electrical/pvPower')"
        />
      </v-col>
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <PowerBlock
          name="Grid power"
          :value="useValue('electrical/shorePower')"
          :history="useLast24Hours('electrical/shorePower')"
        />
      </v-col>
      <v-col
        cols="12"
        sm="6"
        md="4"
        lg="3"
        xl="2"
      >
        <PowerBlock
          name="Power consumption"
          :value="useValue('electrical/totalPowerConsumption')"
          :history="useLast24Hours('electrical/totalPowerConsumption')"
        />
      </v-col>
    </v-row>
  </v-card>
</template>
