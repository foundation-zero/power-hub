<template>
  <v-card
    height="100%"
    width="100%"
    :class="{ scrollable }"
  >
    <v-card-title class="pa-0">
      <v-btn
        variant="text"
        color="blue"
        size="small"
        class="text-mono px-0"
        @click="show = false"
        >&#10094; Back to mapping
      </v-btn>

      <h5 class="text-h5">{{ title }}</h5>

      <v-divider class="mt-3" />
    </v-card-title>

    <v-card-text
      class="pa-0 pb-3"
      @touchmove="onTouchMove"
    >
      <carousel
        v-model="currentSlide"
        :items-to-show="1"
      >
        <slide
          v-for="(slide, index) in slides"
          :key="index"
        >
          <v-sheet>
            <component :is="slide" />
          </v-sheet>
        </slide>
      </carousel>
    </v-card-text>

    <v-divider />

    <ContentPagination
      v-model="currentPage"
      :amount-of-pages="slides.length"
      class="w-100 mt-3"
    />
  </v-card>
</template>

<script setup lang="ts">
import "vue3-carousel/dist/carousel.css";
import { Carousel, Slide } from "vue3-carousel";
import ContentPagination from "./ContentPagination.vue";
import { ref } from "vue";
import { computed } from "vue";
import type { Journey } from "@/types";
import electrical from "./slides/electrical";
import { toRefs } from "vue";
import thermal from "./slides/thermal";
import water from "./slides/water";

const currentPage = ref(1);

const show = defineModel<boolean>();
const props = defineProps<{ journey?: Journey; scrollable?: boolean }>();
const { journey } = toRefs(props);

const titles: Record<Journey, string> = {
  electrical: "Electric energy",
  heat: "Thermal energy",
  water: "Water management",
};

const title = computed(() => (journey.value ? titles[journey.value] : ""));

const slides = computed(() => {
  switch (journey.value) {
    case "electrical":
      return electrical;
    case "heat":
      return thermal;
    case "water":
      return water;
    default:
      return [];
  }
});

const currentSlide = computed({
  get() {
    return currentPage.value - 1;
  },
  set(val: number) {
    currentPage.value = val + 1;
  },
});

const onTouchMove = (event: TouchEvent) => event.stopImmediatePropagation();
</script>

<style scoped lang="scss">
:deep(.carousel__slide),
:deep(.carousel__track),
:deep(.carousel__viewport) {
  height: 100%;
}

:deep(.carousel__slide) {
  align-items: start;
}

.carousel:not(.is-dragging):not(.is-sliding) :deep(.carousel__track) {
  transition: transform 500ms ease !important;
}

:deep(.carousel__slide--next) {
  height: 0;
}
</style>
