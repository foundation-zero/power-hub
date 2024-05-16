<template>
  <div>
    <div class="d-flex align-end justify-space-between">
      <div class="d-flex align-end mb-1">
        <v-icon
          size="32"
          :icon="icon"
        ></v-icon>
        <span class="ml-1 text-h6 font-weight-regular">{{ title }}</span>
      </div>
      <div v-if="unit">
        <animated-number
          class="text-h6 font-weight-regular"
          :to="value"
          :format="format"
        ></animated-number>
        {{ unit }}
      </div>
    </div>
    <v-progress-linear
      class="mt-1"
      :color="color"
      :bg-color="trackColor ?? 'grey'"
      height="15"
      :max="max"
      :model-value="value"
      rounded
    >
    </v-progress-linear>
  </div>
</template>

<script setup lang="ts">
import AnimatedNumber from "vue-number-animation";

defineProps<{
  icon: string;
  title: string;
  value?: number;
  trackColor?: string;
  format?: (val: number) => number | string;
  min?: number;
  max: number;
  unit?: string;
  color: string;
}>();
</script>
