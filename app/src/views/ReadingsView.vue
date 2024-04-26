<template>
  <v-container>
    <Suspense>
      <template #default>
        <AllTables />
      </template>
      <template #fallback>
        <h1>Connecting to PowerHub...</h1>
      </template>
    </Suspense>
  </v-container>
</template>

<script setup lang="ts">
import AllTables from "@/components/AllTables.vue";
</script>
