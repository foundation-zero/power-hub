<template>
  <DataBlock
    color="blue-lighten-1"
    :name="name"
    :value="flow"
    :history="history"
    unit="L/min"
  >
    <template #bottom>
      <div class="text-subtitle-2">
        {{ status ?? "&nbsp;" }}
      </div>
      <div class="d-flex align-center">
        <div class="text-subtitle-2">
          <v-icon
            icon="fa-snowflake"
            size="12"
          />
          <AnimatedNumber
            class="ml-1"
            :to="value?.coldTemperature"
            :from="0"
            :format="format"
          />&deg;
        </div>

        <div class="text-subtitle-2 ml-2">
          <v-icon
            icon="fa-fire-flame-curved"
            size="12"
          />
          <AnimatedNumber
            class="ml-1"
            :to="value?.hotTemperature"
            :from="0"
            :format="format"
          />&deg;
        </div>
      </div>
    </template>
  </DataBlock>
</template>

<script setup lang="ts">
import AnimatedNumber from "vue-number-animation";
import DataBlock from "./DataBlock.vue";
import type { ValueObject } from "@/types";
import { map, type Observable } from "rxjs";
import { useObservable } from "@vueuse/rxjs";
import type { FlowPort } from "@/types/power-hub";
import { formattedNumber } from "@/utils/numbers";

const props = defineProps<{
  name: string;
  value: Observable<FlowPort>;
  flow: Observable<number>;
  status?: string;
  history?: Observable<ValueObject[]>;
}>();

const format = formattedNumber(1);
const value = useObservable(props.value);
const flow = useObservable(props.flow.pipe(map((val) => val * 60)));
</script>
