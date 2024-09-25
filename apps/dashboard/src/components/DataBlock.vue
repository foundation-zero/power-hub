<template>
  <v-card
    :color="color"
    variant="tonal"
    width="100%"
    height="160"
    class="d-flex flex-column justify-space-between py-2 px-5"
  >
    <div class="position-absolute background">
      <slot name="background">
        <AreaChart
          v-if="historicalData"
          :data="historicalData"
          :max="max"
          :min="min"
        />
      </slot>
    </div>

    <div class="text-h6">
      {{ name }}
    </div>

    <div class="text-center">
      <slot name="value">
        <span class="text-h2 font-weight-bold ml-1">
          <AnimatedNumber
            v-if="value !== undefined"
            :to="value"
            :from="0"
            :format="parseInt"
          />
          <span v-else>-</span>
        </span>
      </slot>
      <slot
        v-if="value !== undefined"
        name="unit"
      >
        <span class="text-h5 font-weight-thin ml-2">{{ unit }}</span>
      </slot>
    </div>

    <div class="d-flex justify-space-between">
      <slot name="bottom">
        <span>&nbsp;</span>
      </slot>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import AnimatedNumber from "vue-number-animation";
import type { Unit, ValueObject } from "@shared/types";
import { type Observable } from "rxjs";
import { useObservable } from "@vueuse/rxjs";
import AreaChart from "./AreaChart.vue";

const props = defineProps<{
  name: string;
  color: string;
  value?: number;
  history?: Observable<ValueObject[]>;
  max?: number;
  min?: number;
  unit: Unit;
}>();

const historicalData = props.history ? useObservable(props.history) : undefined;
</script>

<style lang="scss" scoped>
.background {
  left: 0;
  right: 0;
  bottom: 0;
  top: 0;
}
</style>
