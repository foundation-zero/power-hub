<template>
  <v-bottom-sheet
    v-model:model-value="show"
    :opacity="scrimOpacity"
    height="calc(100vh - 64px)"
  >
    <div
      ref="container"
      class="h-100 d-flex justify-center align-end"
    >
      <v-card
        ref="target"
        height="100%"
        width="100%"
        max-width="600"
        max-height="800"
        class="px-5 py-3 d-flex flex-column align-start"
        :class="{ dragging }"
        :style="{ transform: `translateY(${swipeY}px)` }"
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
    </div>
  </v-bottom-sheet>
</template>

<script setup lang="ts">
import { useSwipe } from "@vueuse/core";
import { ref } from "vue";
import { computed } from "vue";

const show = defineModel<boolean>({
  set(val) {
    if (!val) {
      setTimeout(() => {
        swipeY.value = 0;
        prevY.value = 0;
      }, 500);
    }
  },
});

const target = ref<HTMLElement>();
const container = ref<HTMLElement>();

const prevY = ref(0);
const swipeY = ref(0);
const dragging = ref(false);

const scrimOpacity = computed(() =>
  !container.value || !dragging.value
    ? 0.32
    : 0.32 *
      ((container.value.offsetHeight - Math.abs(swipeY.value)) / container.value.offsetHeight),
);

const { direction, lengthY } = useSwipe(target, {
  passive: true,
  onSwipeStart() {
    dragging.value = true;
  },
  onSwipe: () => {
    if (direction.value === "down") {
      prevY.value = swipeY.value;
      swipeY.value = Math.abs(lengthY.value);
    }
  },
  onSwipeEnd() {
    dragging.value = false;

    if (
      direction.value === "down" &&
      container.value?.offsetHeight &&
      (swipeY.value - prevY.value > 20 ||
        Math.abs(lengthY.value) > container.value.offsetHeight / 2)
    ) {
      show.value = false;
      swipeY.value = container.value.offsetHeight;
    } else {
      swipeY.value = 0;
      prevY.value = 0;
    }
  },
});
</script>

<style lang="scss" scoped>
.v-card {
  will-change: transform;
}

.v-card:not(.dragging) {
  transition: transform 500ms ease;
}
</style>
