<template>
  <v-dialog
    v-model="show"
    width="600"
    height="800"
  >
    <v-card
      height="100%"
      width="100%"
      class="px-8 py-3 d-flex flex-column align-start"
    >
      <v-btn
        variant="text"
        color="blue"
        size="small"
        class="text-mono mx-0 px-0"
        @click="show = false"
        >&#10094; Back to mapping
      </v-btn>
      <slot />
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
const show = defineModel<boolean>();
</script>
