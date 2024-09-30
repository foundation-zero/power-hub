<script setup lang="ts">
import PowerHubSetpoints from "@dashboard/components/PowerHubSetpoints.vue";
</script>

<template>
  <v-layout>
    <v-main>
      <v-container>
        <h2 class="text-h2 font-weight-bold">HMI Setpoints</h2>
        <Suspense>
          <PowerHubSetpoints />
        </Suspense>
      </v-container>
    </v-main>
  </v-layout>
</template>
