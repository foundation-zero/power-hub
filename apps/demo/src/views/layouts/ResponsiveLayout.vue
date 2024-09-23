<template>
  <slot
    v-if="view === 'portrait'"
    name="portrait"
  />
  <slot
    v-if="view === 'landscape'"
    name="landscape"
  />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useDisplay } from "vuetify";

const { mdAndUp, width, height } = useDisplay();

const view = computed(() => {
  if (mdAndUp.value && width.value > height.value) {
    return "landscape";
  }

  return "portrait";
});
</script>
