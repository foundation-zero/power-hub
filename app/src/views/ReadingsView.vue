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
import { useObservable } from "@vueuse/rxjs";

const store = usePowerHubStore();
const { connections } = await store.connect();

const tables: DataTable[] = [
  {
    name: "Chiller",
    rows: [
      [
        "Chilled (in) - Temperature",
        useObservable(connections.useMqtt("chiller/chilled_in/temperature")),
      ],
      ["Chilled (in) - Flow", useObservable(connections.useMqtt("chiller/chilled_in/flow"))],
      [
        "Chilled (out) - Temperature",
        useObservable(connections.useMqtt("chiller/chilled_out/temperature")),
      ],
      ["Chilled (out) - Flow", useObservable(connections.useMqtt("chiller/chilled_out/flow"))],
    ],
  },
];
</script>
