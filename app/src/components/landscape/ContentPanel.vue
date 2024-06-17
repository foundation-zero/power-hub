<template>
  <v-navigation-drawer
    v-model:modelValue="show"
    temporary
    color="transparent"
    location="right"
    width="600"
    :scrim="scrim"
    elevation="0"
    border="0"
    style="max-width: 40%"
  >
    <div
      ref="target"
      class="h-100"
    >
      <v-card
        class="h-100"
        :class="{ dragging }"
        :style="{ transform: `translateX(${swipeX}px)` }"
      >
        <v-card-title>
          <v-btn
            variant="text"
            color="blue"
            class="text-mono"
            @click="show = false"
            >&#10094; Back to mapping
          </v-btn>
        </v-card-title>
      </v-card>
    </div>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@/stores/presentation";
import { useSwipe } from "@vueuse/core";
import { computed, ref } from "vue";
import { toRefs } from "vue";

const { setJourney } = usePresentationStore();
const { currentJourney } = toRefs(usePresentationStore());

const target = ref<HTMLElement>();

const show = computed({
  get() {
    return !!currentJourney.value;
  },
  set(val: boolean) {
    if (!val) {
      setJourney();
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
      setJourney();
      swipeX.value = target.value.offsetWidth;
      setTimeout(() => {
        setJourney();
        swipeX.value = 0;
        prevX.value = 0;
      }, 500);
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
