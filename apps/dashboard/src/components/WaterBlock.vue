<template>
  <DataBlock
    :name="name"
    :value="value"
    :color="fillColor"
    :history="history"
    :max="1"
    unit="L"
  >
    <template #bottom>
      <div class="text-subtitle-2">{{ status ?? "&nbsp;" }}</div>

      <div class="d-flex align-center">
        <ThresholdAlarm
          v-if="thresholds?.[0]"
          :threshold="thresholds?.[0]"
          icon="far fa-bell"
          unit="L"
        />
        <ThresholdAlarm
          v-if="thresholds?.[1]"
          class="ml-2"
          :threshold="thresholds?.[1]"
          unit="L"
        />
      </div>
    </template>
  </DataBlock>
</template>

<script setup lang="ts">
import { computed, toRefs } from "vue";
import ThresholdAlarm from "./ThresholdAlarm.vue";
import DataBlock from "./DataBlock.vue";
import { map, type Observable } from "rxjs";
import { useObservable } from "@vueuse/rxjs";
import type { ValueObject } from "@/types";

const props = defineProps<{
  name: string;
  color: string;
  value: Observable<number>;
  max: number;
  status?: string;
  thresholds?: [min?: number, max?: number];
  history?: Observable<ValueObject[]>;
}>();

const { thresholds, color } = toRefs(props);
const value = useObservable(props.value.pipe(map((val) => val * props.max)));

const isWithinThresholds = computed(() => {
  if (!thresholds.value || value.value === undefined) return true;

  const val = value.value;

  const [min, max] = thresholds.value;

  return (min === undefined || val >= min) && (max === undefined || val <= max);
});

const fillColor = computed(() => (isWithinThresholds.value ? color.value : "red"));
</script>
