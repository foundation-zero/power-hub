<template>
  <div class="mt-5">
    <div class="d-flex justify-space-between">
      <v-icon
        :icon="series[0].icon"
        :size="32"
      />
      <v-icon
        :icon="series[1].icon"
        :size="32"
      />
    </div>
    <div class="bar my-3">
      <div
        class="container h-100 w-100 d-flex"
        :class="{ 'bg-grey-lighten-2': disabled }"
      >
        <template v-if="!disabled">
          <div
            :style="{
              backgroundColor: series[0].color,
              width: `${fillPercentage}%`,
            }"
            class="series"
          />

          <div
            :style="{
              backgroundColor: series[1].color,
              width: `${100 - fillPercentage}%`,
            }"
            class="series"
          />
        </template>
      </div>

      <div
        class="marker d-flex flex-column align-center justify-space-between"
        :style="{ left }"
      >
        <div class="pointer"></div>
        <div class="value">
          <span class="text-body-1 font-weight-bold">{{ formattedInt(fillPercentage) }}</span>
          <span class="unit text-subtitle-2">%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formattedInt } from "@/utils/numbers";
import { computed } from "vue";

export type BarSeries = {
  icon: string;
  color: string;
};

const fillTotal = computed(() => props.values[0] + props.values[1]);

const fillPercentage = computed(() =>
  fillTotal.value === 0 ? 0 : (props.values[0] / fillTotal.value) * 100,
);

const left = computed(() => `max(10px, min(calc(100% - 10px), ${fillPercentage.value}%))`);

const props = defineProps<{
  series: [BarSeries, BarSeries];
  values: [number, number];
  disabled?: boolean;
}>();
</script>

<style lang="scss" scoped>
.container {
  border-radius: 10px;
  overflow: hidden;

  & > :not(:last-child) {
    border-right: 4px double white;
  }
}

.bar {
  height: 16px;
  position: relative;
}

.series {
  min-width: 10px;
  max-width: calc(100% - 10px);
  transition: width 750ms ease;
  will-change: width;
  height: 100%;
}

.marker {
  will-change: left;
  transition: left 750ms ease;
  height: 54px;
  top: -15px;
  position: absolute;
  transform: translate(calc(-50% - 2px));
}

.value {
  transform: translate(7px, 0);
}

.pointer {
  content: "";
  width: 0;
  height: 0;
  border-top: 10px solid black;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
}
</style>
