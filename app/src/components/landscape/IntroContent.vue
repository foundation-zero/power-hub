<template>
  <div class="d-flex h-100">
    <v-sheet
      color="#FF8C2E"
      dark
      width="240"
      height="100%"
      class="pa-8"
    >
      <svg
        width="100%"
        viewBox="0 0 198 59"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <FZLogo />
      </svg>
    </v-sheet>
    <IntroContent class="d-flex flex-column justify-center w-100" />
  </div>
</template>

<script setup lang="ts">
import FZLogo from "../FZLogo.vue";
import IntroContent from "../responsive/IntroContent.vue";
</script>
