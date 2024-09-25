<template>
  <div
    ref="el"
    class="h-100 w-100 d-flex justify-center"
    :style="{ backgroundImage }"
  >
    <div
      class="w-100 h-100"
      :style="{ maxWidth: position ? `${height * (ratio ?? 1)}px` : undefined }"
    >
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Direction } from "@demo/types";
import { computed } from "vue";
import { ref } from "vue";
import { useDisplay } from "vuetify";

const { position } = defineProps<{ backgroundImage?: string; position?: Direction }>();
const display = useDisplay();

const el = ref<HTMLElement>();

const ratio = computed(() => {
  switch (position) {
    case "right":
      return 563 / 972;
    case "left":
      return 590 / 972;
    default:
      return 1;
  }
});

const height = computed(() => Math.min(display.height.value, el.value?.offsetHeight ?? 0));
</script>

<style scoped lang="scss">
div {
  background-position: center center;
  background-repeat: no-repeat;
  background-size: cover;
}
</style>
