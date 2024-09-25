<template>
  <DataBlock
    :color="color"
    :name="name"
    :value="value"
    :history="history"
    :max="40"
    unit="&deg;"
  >
    <template
      v-if="setPoint"
      #bottom
    >
      <div class="text-caption">
        <span class="font-weight-thin">Set to </span>

        <span class="font-weight-bold text-subtitle-2">
          <AnimatedNumber
            :to="setPoint"
            :from="0"
            :format="parseInt"
          />&deg;
        </span>
      </div>
    </template>

    <template #unit>
      <sup class="text-h4 font-weight-thin">&deg;</sup>
    </template>
  </DataBlock>
</template>

<script setup lang="ts">
import { computed } from "vue";
import AnimatedNumber from "vue-number-animation";
import DataBlock from "./DataBlock.vue";
import type { ValueObject } from "@shared/types";
import type { Observable } from "rxjs";
import { useObservable } from "@vueuse/rxjs";

const props = defineProps<{
  name: string;
  setPoint?: Observable<number>;
  value: Observable<number>;
  history?: Observable<ValueObject[]>;
}>();

const value = useObservable(props.value);
const setPoint = props.setPoint ? useObservable(props.setPoint) : undefined;

const color = computed(() => {
  if (value.value! >= 30) return "red-lighten-1";
  if (value.value! >= 25) return "warning";
  return "cyan";
});
</script>
