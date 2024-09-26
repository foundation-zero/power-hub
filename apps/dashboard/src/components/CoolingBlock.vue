<template>
  <DataBlock
    :name="name"
    color="teal"
    :unit="unit"
    :value="value"
    :history="history"
    :min="min"
  >
    <template
      v-if="status"
      #bottom
    >
      <div class="text-subtitle-2">
        {{ status }}
      </div>
      <div
        v-if="props.powerIn || props.powerOut"
        class="d-flex align-center"
      >
        <div>
          <v-icon
            icon="fa fa-arrow-down"
            size="10"
          />
          <AnimatedNumber
            class="ml-1 text-subtitle-2"
            :to="powerIn"
            :from="0"
            :format="parseInt"
          />
          <span class="text-caption ml-1">{{ powerInUnit }}</span>
        </div>

        <div class="ml-2">
          <v-icon
            icon="fa fa-arrow-up"
            size="10"
          />
          <AnimatedNumber
            class="ml-1 text-subtitle-2"
            :to="powerOut"
            :from="0"
            :format="parseInt"
          /><span class="text-caption ml-1">{{ powerOutUnit }}</span>
        </div>
      </div>
    </template>
  </DataBlock>
</template>

<script setup lang="ts">
import AnimatedNumber from "vue-number-animation";
import { useAsWatts } from "@shared/utils";
import DataBlock from "./DataBlock.vue";
import { type Observable } from "rxjs";
import type { ValueObject } from "@shared/types";
import { useObservable } from "@vueuse/rxjs";
import { ref } from "vue";

const props = defineProps<{
  name: string;
  value: Observable<number>;
  powerIn?: Observable<number>;
  powerOut?: Observable<number>;
  status?: string;
  min?: number;
  history?: Observable<ValueObject[]>;
}>();

const { value, unit } = useAsWatts(useObservable(props.value), 10_000);
const { value: powerIn, unit: powerInUnit } = useAsWatts(
  props.powerIn ? useObservable(props.powerIn) : ref(),
  10_000,
);

const { value: powerOut, unit: powerOutUnit } = useAsWatts(
  props.powerOut ? useObservable(props.powerOut) : ref(),
  10_000,
);
</script>
