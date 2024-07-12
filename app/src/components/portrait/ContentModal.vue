<template>
  <v-dialog
    v-model="show"
    max-width="500"
    height="700"
    max-height="90%"
    scrollable
  >
    <slot :show="show" />
  </v-dialog>
</template>

<script setup lang="ts">
const show = defineModel<boolean>();
</script>
