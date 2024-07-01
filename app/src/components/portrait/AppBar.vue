<template>
  <v-app-bar
    flat
    elevation="1"
    class="pr-4"
  >
    <v-app-bar-title>
      <v-btn
        to="/"
        flat
        variant="text"
        class="text-uppercase text-subtitle-1"
        >Power Hub</v-btn
      >
    </v-app-bar-title>
    <FZeroButton />
  </v-app-bar>
</template>

<script setup lang="ts">
import FZeroButton from "../FZeroButton.vue";
</script>
