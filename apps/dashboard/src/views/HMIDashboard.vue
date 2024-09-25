<script setup lang="ts">
import DashboardItems from "@dashboard/components/DashboardItems.vue";
</script>

<template>
  <v-layout>
    <v-main>
      <v-container>
        <h2 class="text-h2 font-weight-bold">HMI Dashboard</h2>
        <Suspense>
          <DashboardItems />
        </Suspense>
      </v-container>
    </v-main>
  </v-layout>
</template>
