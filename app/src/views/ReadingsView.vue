<template>
  <ReadingsTable
    v-for="table in tables"
    :key="table.name"
    :name="table.name"
    :rows="table.rows"
  ></ReadingsTable>
</template>

<script setup lang="ts">
import ReadingsTable from "@/components/ReadingsTable.vue";
import type { DataTable } from "@/types";
import { usePowerHubStore } from "@/stores/power-hub";

const store = usePowerHubStore();
const { useConnection } = await store.connect();

const tables: DataTable[] = [
  {
    name: "Chiller",
    rows: [
      ["Chilled (in) - Temperature", useConnection("chiller/CHILLED_IN/temperature")],
      ["Chilled (in) - Flow", useConnection("chiller/CHILLED_IN/flow")],
      ["Chilled (out) - Temperature", useConnection("chiller/CHILLED_OUT/temperature")],
      ["Chilled (out) - Flow", useConnection("chiller/CHILLED_OUT/flow")],
    ],
  },
];
</script>
