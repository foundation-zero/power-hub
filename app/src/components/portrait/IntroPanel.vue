<template>
  <v-bottom-sheet
    v-model:model-value="show"
    fullscreen
  >
    <slot />
  </v-bottom-sheet>
</template>

<script setup lang="ts">
const show = defineModel<boolean>();
</script>
