<template>
  <h3 :class="{ 'text-h4': $vuetify.display.mdAndUp, 'text-h5': $vuetify.display.smAndDown }">
    Welcome to the<br />
    Power Hub, this display takes<br />
    you through the technology of<br />
    the power hub
  </h3>

  <div>
    <v-btn
      rounded="0"
      flat
      color="white"
      class="mt-12 text-mono font-weight-regular"
      @click="start"
      >Start here &#10095;</v-btn
    >
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();

const start = () => router.push("/journeys");
</script>
