<script setup lang="ts">
import { replaceAll } from "@/utils";
import { useObservable } from "@vueuse/rxjs";
import { snakeCase } from "lodash";
import { map, Observable } from "rxjs";

const props = defineProps<{
  data: Observable<Record<string, any>>;
}>();

const getValue = (key: string, value: any) => {
  if (typeof value === "string") return replaceAll(snakeCase(value), "_", " ");
  if (key === "time") return new Date(value).toLocaleString();
};

const rows = useObservable(
  props.data.pipe(
    map((val) =>
      Object.entries(val).map(([key, value]) => ({
        key: replaceAll(snakeCase(key), "_", " "),
        value: getValue(key, value),
      })),
    ),
  ),
);
</script>

<template>
  <v-table class="text-capitalize">
    <tbody>
      <tr
        v-for="row in rows"
        :key="row.key"
      >
        <th>{{ row.key }}</th>
        <td>{{ row.value }}</td>
      </tr>
    </tbody>
  </v-table>
</template>
