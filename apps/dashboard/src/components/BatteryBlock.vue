<template>
  <DataBlock
    color="yellow"
    :name="name"
    :value="value"
    :history="history"
    :max="1"
    unit="%"
  >
    <template #bottom>
      <div class="d-flex align-center">
        <v-icon
          :icon="icon"
          size="16"
          class="mr-1"
        />
        {{ status }}
      </div>
    </template>
  </DataBlock>
</template>

<script setup lang="ts">
import { computed } from "vue";
import DataBlock from "./DataBlock.vue";
import type { ValueObject } from "@/types";
import { map, type Observable } from "rxjs";
import { useObservable } from "@vueuse/rxjs";

const props = defineProps<{
  name: string;
  value: Observable<number>;
  chargeState: Observable<0 | 1 | 2>;
  history?: Observable<ValueObject[]>;
}>();

const value = useObservable(props.value.pipe(map((val) => val * 100)));
const chargeState = useObservable(props.chargeState);

const icon = computed(() => {
  if (!value.value) return "";

  const chargePercentage = Math.round(value.value / 10) * 10;

  if (chargePercentage === 100) return "mdi:mdi-battery";

  switch (chargeState.value) {
    case 2:
      return `mdi:mdi-battery-charging-${chargePercentage}`;
    case 1:
      return chargePercentage === 100 ? "mdi:mdi-battery" : `mdi:mdi-battery-${chargePercentage}`;
    default:
      return "mdi:mdi-battery-unknown";
  }
});

const status = computed(() => {
  if (!chargeState.value) return "";

  switch (chargeState.value) {
    case 2:
      return "Charging";
    case 1:
      return "Discharging";
    default:
      return "Idle";
  }
});
</script>
