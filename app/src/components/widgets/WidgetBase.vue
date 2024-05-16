<template>
  <v-card
    rounded="0"
    elevation="3"
    class="pt-4 pb-8 px-6"
  >
    <div class="d-flex justify-space-between">
      <span class="text-h6 text-uppercase font-weight-medium">{{ title }}</span>
      <div>
        <AnimatedNumber
          v-if="value"
          :to="value"
          :format="format"
          class="text-h3 font-weight-medium"
        />
        <span
          v-if="unit"
          class="text-h6 font-weight-regular ml-2"
          >{{ unit }}</span
        >
        <v-icon
          v-if="icon"
          size="24"
          :icon="icon"
        ></v-icon>
      </div>
    </div>
    <div>
      <slot name="default"></slot>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import AnimatedNumber from "vue-number-animation";

defineProps<{
  title: string;
  unit?: string;
  icon?: string;
  format?: (val: number) => string | number;
  value?: string | number;
}>();
</script>
