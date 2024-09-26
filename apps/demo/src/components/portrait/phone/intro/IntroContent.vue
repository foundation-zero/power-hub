<template>
  <v-sheet
    color="#FF8C2E"
    dark
    rounded="0"
    elevation="0"
    height="100%"
  >
    <carousel
      v-model="currentSlide"
      class="w-100 h-100"
      :items-to-show="1"
    >
      <slide
        v-for="(slide, index) in slides"
        :key="index"
        class="h-100"
      >
        <component :is="slide" />
      </slide>
    </carousel>

    <IntroPagination
      v-model="currentPage"
      :amount-of-pages="slides.length"
      class="w-100 mt-3"
    />

    <v-btn
      v-show="currentPage < slides.length"
      variant="text"
      class="font-mono"
      size="small"
      to="/journeys"
      >Skip intro &gt;</v-btn
    >
  </v-sheet>
</template>

<script setup lang="ts">
import { Carousel, Slide } from "vue3-carousel";
import IntroPagination from "@demo/components/responsive/IntroPagination.vue";
import WelcomeToThePowerHub from "./WelcomeToThePowerHub.vue";
import WhatThePowerHubProvides from "./WhatThePowerHubProvides.vue";
import ElectricEnergyConverts from "./ElectricEnergyConverts.vue";
import TheSecondPart from "./TheSecondPart.vue";
import ThermalEnergyConverts from "./ThermalEnergyConverts.vue";
import TheThirdPart from "./TheThirdPart.vue";
import WaterManagementIsResponsible from "./WaterManagementIsResponsible.vue";
import WeWillNowExplain from "./WeWillNowExplain.vue";
import { ref } from "vue";
import { computed } from "vue";

const currentSlide = ref(0);

const currentPage = computed({
  get() {
    return currentSlide.value + 1;
  },
  set(val: number) {
    currentSlide.value = val - 1;
  },
});

const slides = [
  WelcomeToThePowerHub,
  WhatThePowerHubProvides,
  ElectricEnergyConverts,
  TheSecondPart,
  ThermalEnergyConverts,
  TheThirdPart,
  WaterManagementIsResponsible,
  WeWillNowExplain,
];
</script>

<style scoped lang="scss">
.v-pagination {
  position: absolute;
  bottom: 20px;
}

.v-btn {
  position: absolute;
  top: 10px;
  right: 10px;
}

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
