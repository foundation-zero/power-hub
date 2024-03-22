<template>
  <h1>{{ name }}</h1>
  <v-card>
    <v-list>
      <v-list-item
        v-for="[title, value] in rows"
        :key="title"
        :title="title"
      >
        <template #append>{{ value }}</template>
      </v-list-item>
    </v-list>
  </v-card>
</template>

<script setup lang="ts">
import type { DataTableRow } from "@/types";

defineProps<{
  rows: DataTableRow[];
  name: string;
}>();
</script>
