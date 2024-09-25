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

      <h5 class="text-h5">Data widgets</h5>

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
        <slide class="1">
          <ProductionChartWidget
            :power-hub="powerhub"
            class="w-100 my-3 mx-1"
          />
        </slide>

        <slide class="2">
          <div class="mx-1 my-3 w-100">
            <CoolingDemandWidget
              :power-hub="powerhub"
              class="w-100"
            />
            <WaterDemandWidget
              :power-hub="powerhub"
              class="w-100 mt-5"
            />
          </div>
        </slide>
      </carousel>
    </v-card-text>

    <v-divider />

    <ContentPagination
      v-model="currentPage"
      :amount-of-pages="2"
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
import ProductionChartWidget from "../widgets/ProductionChartWidget.vue";
import CoolingDemandWidget from "../widgets/CoolingDemandWidget.vue";
import WaterDemandWidget from "../widgets/WaterDemandWidget.vue";
import { usePowerHubStore } from "@shared/stores/power-hub";

const currentPage = ref(1);

const show = defineModel<boolean>();
defineProps<{ scrollable?: boolean }>();

const currentSlide = computed({
  get() {
    return currentPage.value - 1;
  },
  set(val: number) {
    currentPage.value = val + 1;
  },
});

const onTouchMove = (event: TouchEvent) => event.stopImmediatePropagation();

const store = usePowerHubStore();
const powerhub = await store.connect();
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
