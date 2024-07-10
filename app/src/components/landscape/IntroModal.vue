<template>
  <v-dialog
    v-model="show"
    :max-width="maxWidth"
    opacity="0.99"
    scrim="#fff"
    :fullscreen="shouldBeFullscreen"
  >
    <slot :show="show" />
  </v-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useDisplay } from "vuetify";

const show = defineModel<boolean>();

const { width, height } = useDisplay();

const maxWidth = computed(() => Math.min(width.value, (Math.min(1080, height.value) / 9) * 16));

const shouldBeFullscreen = computed(() => width.value <= 1920 && height.value <= 1080);
</script>

<style scoped lang="scss">
.v-dialog > :deep(.v-overlay__content) {
  height: 100%;
}
</style>
