<script setup lang="ts">
import type { PowerHubStore } from "@shared/stores/power-hub";
import ObjectDataTable from "./ObjectDataTable.vue";

const { powerHub } = defineProps<{ powerHub: PowerHubStore }>();
</script>

<template>
  <v-card class="pa-8">
    <h3 class="text-h4 font-weight-thin mb-8 d-flex align-center">
      <v-icon
        size="24"
        icon="fa-gear"
        class="mr-5"
      />
      Control modes
    </h3>

    <ObjectDataTable :data="powerHub.controlModes.useTopic()" />
  </v-card>
</template>
