<template>
  <component
    :is="tag ?? 'span'"
    v-if="to === undefined"
  >
    -
  </component>
  <AnimatedNumber
    v-else
    :from="0"
    :format="formattedInt"
    :to="to"
    :tag="tag"
  />
</template>

<script setup lang="ts">
import { formattedInt } from "@shared/utils/numbers";
import AnimatedNumber from "vue-number-animation";

defineProps<{ to?: number; tag?: string }>();
</script>
