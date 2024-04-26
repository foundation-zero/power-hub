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
const { sensors } = await store.connect();

const tables: DataTable[] = [
  {
    name: "Chiller",
    rows: [
      [
        "Chilled (in) - Temperature",
        useObservable(sensors.useMqtt("chiller/chilled_input_temperature")),
      ],
      ["Chilled - Flow", useObservable(sensors.useMqtt("chiller/chilled_flow"))],
      [
        "Chilled (out) - Temperature",
        useObservable(sensors.useMqtt("chiller/chilled_output_temperature")),
      ],
    ],
  },
];
</script>
