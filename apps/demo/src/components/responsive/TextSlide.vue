<template>
  <div
    class="text-slide"
    :class="{ desktop: $vuetify.display.mdAndUp, mobile: $vuetify.display.smAndDown }"
  >
    <div
      class="title d-flex align-center text-left"
      :class="journey"
    >
      <slot name="title" />
    </div>
    <div class="body mt-3 text-left">
      <slot name="body" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Journey } from "@/types";

defineProps<{ journey: Journey }>();
</script>

<style scoped lang="scss">
.title {
  font-size: 1.9rem;
  min-height: 175px;
  background-position: center right 20px;

  &.water {
    background-image: url("/water.svg");
  }

  &.electrical {
    background-image: url("/electrical.svg");
  }

  &.heat {
    background-image: url("/thermal.svg");
  }
}

.text-slide.desktop :deep(p) {
  line-height: 26px;
  font-size: 18px;
}

.text-slide.mobile :deep(p) {
  font-size: 16px;
  line-height: 21px;
}

:deep(p) {
  margin-top: 16px;
}

:deep(svg) {
  margin-bottom: 32px;
}
</style>
