<script setup lang="ts">
import { toggleSetpoint, useSetpointsStore } from "@dashboard/stores/setpoints";
import { usePowerHubStore } from "@shared/stores/power-hub";
import SetpointsTable from "./SetpointsTable.vue";
import { ref, toRefs, watch } from "vue";
import { onBeforeRouteLeave } from "vue-router";
import { useObservable } from "@vueuse/rxjs";

const isConfirmed = ref(false);
const store = useSetpointsStore();
const { setSetpoint } = await store.connect();
const { isCoolingDown } = toRefs(store);
const powerHub = await usePowerHubStore().connect();

onBeforeRouteLeave(() => store.deactivate());

watch(isCoolingDown, (next, prev) => {
  if (prev === true && next === false) isConfirmed.value = false;
});

const setpoints = useObservable(powerHub.setpoints.useTopic());
</script>

<template>
  <v-row>
    <v-col
      cols="12"
      class="mb-8 mt-12"
    >
      <v-btn
        size="large"
        color="orange"
        variant="tonal"
        :disabled="store.isCoolingDown || !isConfirmed"
        @click="setSetpoint('manualOutboardOn', toggleSetpoint)"
      >
        Turn {{ setpoints?.manualOutboardOn ? "off" : "on" }} outboard pump
      </v-btn>

      <v-checkbox
        v-model="isConfirmed"
        :disabled="store.isCoolingDown"
        :label="store.isCoolingDown ? `Wait for: ${store.coolDownRemaining}` : 'Yes, I\'m sure'"
      />
    </v-col>
    <v-col cols="12">
      <SetpointsTable
        :power-hub="powerHub"
        :included-keys="['manualOutboardOn']"
      />
    </v-col>
  </v-row>
</template>
