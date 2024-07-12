<template>
  <div class="d-flex flex-row">
    <div
      :style="{ width: $slots['right'] ? `${left ?? 60}%` : `${maxWidth ?? '100%'}` }"
      class="h-100 left"
    >
      <slot name="left"></slot>
    </div>
    <div
      v-if="$slots['right']"
      class="h-100"
      :style="{ width: `${100 - (left ?? 60)}%` }"
    >
      <slot name="right"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  left?: number;
  maxWidth?: number | string;
}>();
</script>
