<template>
  <v-sheet
    ref="container"
    color="#FF8C2E"
    dark
    rounded="0"
    elevation="0"
    height="100%"
    @mouseleave="hoverPosition = undefined"
    @mousemove="onMouseMove"
  >
    <carousel
      v-model="currentSlide"
      class="w-100 h-100"
      :items-to-show="1"
    >
      <slide
        v-for="([left, right], index) in slides"
        :key="index"
        class="h-100 text-left"
      >
        <SideBySide
          class="w-100 h-100"
          :left="57.5"
          max-width="75%"
        >
          <template #left>
            <component :is="left" />
          </template>
          <template
            v-if="right"
            #right
          >
            <component :is="right" />
          </template>
        </SideBySide>
      </slide>
    </carousel>

    <IntroPagination
      v-model="currentPage"
      :amount-of-pages="slides.length"
    />

    <v-btn
      v-show="currentPage < slides.length"
      variant="text"
      class="font-mono"
      size="large"
      to="/journeys"
      >Skip intro &gt;</v-btn
    >

    <SwipeButtons
      id="swipe-buttons"
      :swipe-left="hoverPosition === 'left' && currentSlide > 0"
      :swipe-right="hoverPosition === 'right' && currentPage < slides.length"
      @prev="currentPage--"
      @next="currentPage++"
    />

    <FZLogo id="logo" />
  </v-sheet>
</template>

<script setup lang="ts">
import { useDisplay } from "vuetify";
import { VSheet } from "vuetify/components";
import { Carousel, Slide } from "vue3-carousel";
import IntroPagination from "@/components/responsive/IntroPagination.vue";
import WelcomeToThePowerHub from "./WelcomeToThePowerHub.vue";
import WhatThePowerHubProvides from "./WhatThePowerHubProvides.vue";
import ElectricEnergyConverts from "./ElectricEnergyConverts.vue";
import TheSecondPart from "./TheSecondPart.vue";
import ThermalEnergyConverts from "./ThermalEnergyConverts.vue";
import TheThirdPart from "./TheThirdPart.vue";
import WaterManagementIsResponsible from "./WaterManagementIsResponsible.vue";
import WeWillNowExplain from "./WeWillNowExplain.vue";
import SunRise from "./SunRise.vue";
import { ref, computed } from "vue";
import SideBySide from "@/components/responsive/SideBySide.vue";
import SwipeButtons from "@/components/responsive/SwipeButtons.vue";
import FZLogo from "@/components/FZLogo.vue";
import type { Direction } from "@/types";

const currentSlide = ref(0);
const container = ref<VSheet>();
const hoverPosition = ref<Direction>();

const currentPage = computed({
  get() {
    return currentSlide.value + 1;
  },
  set(val: number) {
    currentSlide.value = val - 1;
  },
});

const slides = [
  [WelcomeToThePowerHub, SunRise],
  [WhatThePowerHubProvides, ElectricEnergyConverts],
  [TheSecondPart, ThermalEnergyConverts],
  [TheThirdPart, WaterManagementIsResponsible],
  [WeWillNowExplain],
];

const display = useDisplay();

const onMouseMove = (e: MouseEvent) => {
  if (display.platform.value.touch) return;

  const { x, width } = container.value!.$el.getBoundingClientRect();
  const dx = e.clientX - x;

  if (dx <= width * 0.4) {
    hoverPosition.value = "left";
  } else if (dx >= width * 0.6) {
    hoverPosition.value = "right";
  } else {
    hoverPosition.value = undefined;
  }
};
</script>

<style scoped lang="scss">
#logo {
  position: absolute;
  top: 50px;
  left: 50px;
}

#swipe-buttons {
  position: absolute;
  top: 50%;
  transform: translate(0, -50%);
  left: 50px;
  right: 50px;
}

.v-pagination {
  position: absolute;
  bottom: 50px;
  left: 50px;
}

.v-btn {
  position: absolute;
  top: 50px;
  right: 30px;
}

:deep(.carousel__slide),
:deep(.carousel__track),
:deep(.carousel__viewport) {
  height: 100%;
}

:deep(.carousel__slide) {
  align-items: start;
}

:deep(.carousel__slide--next) {
  height: 0;
}
</style>
