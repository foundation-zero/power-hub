<template>
  <DataBlock
    color="blue-lighten-1"
    :name="name"
    :value="value"
    :history="history"
    unit="L/min"
  >
    <template #bottom>
      <div class="text-subtitle-2">
        {{ status ?? "&nbsp;" }}
      </div>
    </template>
  </DataBlock>
</template>

<script setup lang="ts">
import DataBlock from "./DataBlock.vue";
import type { ValueObject } from "@shared/types";
import { type Observable } from "rxjs";
import { useObservable } from "@vueuse/rxjs";

const props = defineProps<{
  name: string;
  value: Observable<number>;
  status?: string;
  history?: Observable<ValueObject[]>;
}>();

const value = useObservable(props.value);
</script>
