<script setup lang="ts">
import { replaceAll } from "@shared/utils";
import { useObservable } from "@vueuse/rxjs";
import { snakeCase } from "lodash";
import { map, Observable } from "rxjs";

const props = defineProps<{
  data: Observable<Record<string, any>>;
  includedKeys?: string[];
}>();

const getValue = (key: string, value: any) => {
  if (key === "time" || new Date(value).getFullYear() > 1970)
    return new Date(value).toLocaleString();

  if (typeof value === "string") return replaceAll(snakeCase(value), "_", " ");

  return value;
};

const rows = useObservable(
  props.data.pipe(
    map((val) =>
      Object.entries(val)
        .filter(([key]) => !props.includedKeys?.length || props.includedKeys.includes(key))
        .map(([key, value]) => ({
          key: replaceAll(snakeCase(key), "_", " "),
          value: getValue(key, value),
        })),
    ),
  ),
);
</script>

<template>
  <v-table>
    <tbody class="text-capitalize">
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
