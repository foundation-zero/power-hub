<template>
  <v-navigation-drawer
    v-model:modelValue="show"
    temporary
    tile
    color="transparent"
    location="right"
    width="600"
    :scrim="scrim"
    elevation="0"
    :rounded="0"
    border="0"
    style="max-width: 40%"
  >
    <div
      ref="target"
      class="h-100"
    >
      <div
        :class="{ dragging, 'h-100': true }"
        :style="{ transform: `translateX(${swipeX}px)` }"
      >
        <slot />
      </div>
    </div>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { useSwipe } from "@vueuse/core";
import { computed, ref } from "vue";

const target = ref<HTMLElement>();

const show = defineModel<boolean>({
  set(val) {
    if (!val) {
      setTimeout(() => {
        swipeX.value = 0;
        prevX.value = 0;
      }, 500);
    }
  },
});

const prevX = ref(0);
const swipeX = ref(0);
const dragging = ref(false);

const scrim = computed(() =>
  target.value
    ? `rgba(0,0,0,${!dragging.value ? 1 : 1 * ((target.value.offsetWidth - Math.abs(swipeX.value)) / target.value.offsetWidth)})`
    : "#000",
);

const { direction, lengthX } = useSwipe(target, {
  passive: true,
  onSwipeStart() {
    dragging.value = true;
  },
  onSwipe: () => {
    if (direction.value === "right") {
      prevX.value = swipeX.value;
      swipeX.value = Math.abs(lengthX.value);
    }
  },
  onSwipeEnd() {
    dragging.value = false;

    if (
      direction.value === "right" &&
      target.value?.offsetWidth &&
      (swipeX.value - prevX.value > 20 || Math.abs(lengthX.value) > target.value.offsetWidth / 2)
    ) {
      show.value = false;
      swipeX.value = target.value.offsetWidth;
    } else {
      swipeX.value = 0;
      prevX.value = 0;
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
