<template>
  <DataBlock
    color="cyan"
    :name="name"
    :value="value"
    :history="history"
    :max="max"
    unit="&deg;"
  >
    <template #unit>
      <sup class="text-h4 font-weight-thin">&deg;</sup>
    </template>
  </DataBlock>
</template>

<script setup lang="ts">
import DataBlock from "./DataBlock.vue";
import type { ValueObject } from "@/types";
import type { Observable } from "rxjs";
import { useObservable } from "@vueuse/rxjs";

const props = defineProps<{
  name: string;
  max?: number;
  value: Observable<number>;
  history?: Observable<ValueObject[]>;
}>();

const value = useObservable(props.value);
</script>
