<template>
  <DataBlock
    :name="name"
    color="yellow"
    :unit="unit"
    :value="value"
    :history="history"
  >
  </DataBlock>
</template>

<script setup lang="ts">
import { useAsWatts } from "@/utils";
import DataBlock from "./DataBlock.vue";
import type { Observable } from "rxjs";
import type { ValueObject } from "@/types";
import { useObservable } from "@vueuse/rxjs";

const props = defineProps<{
  name: string;
  value: Observable<number>;
  history?: Observable<ValueObject[]>;
}>();

const { value, unit } = useAsWatts(useObservable(props.value));
</script>
