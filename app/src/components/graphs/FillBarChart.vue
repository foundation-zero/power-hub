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
    <div class="bar d-flex mt-3 mb-3">
      <div
        :style="{ backgroundColor: series[0].color, width: `${fillPercentage}%` }"
        class="series d-flex pl-3 align-center"
      >
        <div class="pointer"></div>
        <div class="value">
          <span class="text-body-1 font-weight-bold">{{ formattedInt(fillPercentage) }}</span>
          <span class="unit text-subtitle-2">%</span>
        </div>
      </div>
      <div
        :style="{ backgroundColor: series[1].color, width: `${100 - fillPercentage}%` }"
        class="series d-flex pl-3 align-center"
      ></div>
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

const fillPercentage = computed(
  () => (props.values[0] / (props.values[0] + props.values[1])) * 100,
);

const props = defineProps<{
  series: [BarSeries, BarSeries];
  values: [number, number];
}>();
</script>

<style lang="scss" scoped>
.bar {
  height: 16px;

  & > :first-child {
    border-top-left-radius: 10px;
    border-bottom-left-radius: 10px;
    border-right: 4px double white;
  }

  & > :last-child {
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
  }
}

.series {
  position: relative;
  transition: width 750ms ease;
  will-change: width;
  height: 100%;
  display: inline-block;
}

.value {
  position: absolute;
  bottom: -6px;
  right: -8px;
  text-align: center;
  transform: translate(50%, 100%);
}

.pointer {
  position: absolute;
  content: "";
  width: 0;
  height: 0;
  right: -2px;
  top: -3px;
  transform: translate(50%, -100%);
  border-top: 10px solid black;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
}
</style>
