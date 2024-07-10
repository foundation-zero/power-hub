<template>
  <v-dialog
    v-model="show"
    width="calc(100% - 64px)"
    height="calc(100% - 64px)"
    opacity="1"
    scrim="#FFF"
    elevation="0"
    max-height="calc(1920px - 128px)"
    max-width="calc(1080px - 128px)"
    scrollable
  >
    <slot :show="show" />
  </v-dialog>
</template>

<script setup lang="ts">
const show = defineModel<boolean>();
</script>
