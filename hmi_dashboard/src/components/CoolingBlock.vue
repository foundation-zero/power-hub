<template>
  <DataBlock
    :name="name"
    color="teal"
    :unit="unit"
    :value="value"
    :history="history"
    :min="0"
  >
    <template
      v-if="status"
      #bottom
    >
      <div class="text-subtitle-2">
        {{ status }}
      </div>
    </template>
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
  status?: string;
  history?: Observable<ValueObject[]>;
}>();

const { value, unit } = useAsWatts(useObservable(props.value), 10000);
</script>
