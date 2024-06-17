<template>
  <v-bottom-sheet
    v-model:model-value="show"
    :scrim="scrim"
    height="calc(100vh - 64px)"
  >
    <div
      ref="target"
      class="h-100"
    >
      <v-card
        height="100%"
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

        <h5 class="text-h5">Thermal energy</h5>

        <v-divider class="mt-3 w-100" />

        <carousel
          :items-to-show="1"
          class="w-100 mt-3 flex-grow-1"
        >
          <slide
            v-for="slide in 3"
            :key="slide"
          >
            <v-sheet
              width="calc(100vw - 32px)"
              class="text-left"
            >
              <p class="text-h6">From the battery we feed heat into the absorption chiller....</p>
              <BatteryGauge
                width="calc(100vw - 48px)"
                class="mt-5"
              />
            </v-sheet>
          </slide>
        </carousel>
      </v-card>
    </div>
  </v-bottom-sheet>
</template>

<script setup lang="ts">
import "vue3-carousel/dist/carousel.css";
import { Carousel, Slide } from "vue3-carousel";
import { usePresentationStore } from "@/stores/presentation";
import { useSwipe } from "@vueuse/core";
import { ref } from "vue";
import { computed } from "vue";
import { toRefs } from "vue";
import BatteryGauge from "../gauges/BatteryGauge.vue";

const { currentJourney } = toRefs(usePresentationStore());
const { setJourney } = usePresentationStore();
const target = ref<HTMLElement>();

const show = computed({
  get() {
    return !!currentJourney.value;
  },
  set(val: boolean) {
    if (!val) {
      swipeY.value = 0;
      setJourney();
    }
  },
});

const swipeY = ref(0);
const dragging = ref(false);

const scrim = computed(() =>
  target.value
    ? `rgba(0,0,0,${!dragging.value ? 1 : 1 * ((target.value.offsetHeight - Math.abs(swipeY.value)) / target.value.offsetHeight)})`
    : "#000",
);

const prevY = ref(0);

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
      target.value?.offsetHeight &&
      (swipeY.value - prevY.value > 20 || Math.abs(lengthY.value) > target.value.offsetHeight / 2)
    ) {
      setJourney();
      swipeY.value = target.value.offsetHeight;
      setTimeout(() => {
        setJourney();
        swipeY.value = 0;
        prevY.value = 0;
      }, 500);
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
