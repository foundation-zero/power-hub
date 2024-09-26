<template>
  <ResponsiveLayout>
    <template #landscape>
      <LandscapeView />
    </template>
    <template #portrait>
      <PortraitView />
    </template>
  </ResponsiveLayout>
</template>

<script setup lang="ts">
import { watch } from "vue";
import { defineAsyncComponent } from "vue";
import { toRefs } from "vue";
import { usePresentationStore } from "@demo/stores/presentation";
import { activate, show } from "@demo/utils";
import { useRoute } from "vue-router";
import type { Journey } from "@demo/types";
import ResponsiveLayout from "./layouts/ResponsiveLayout.vue";

const PortraitView = defineAsyncComponent(() => import("./portrait/MapView.vue"));
const LandscapeView = defineAsyncComponent(() => import("./landscape/MapView.vue"));

const route = toRefs(useRoute());

const { setJourney } = usePresentationStore();
const { currentJourney, componentStates, streamStates } = toRefs(usePresentationStore());

watch(
  route.params,
  (val, prev) => {
    if (val.journey !== prev?.journey) {
      setJourney(val.journey as Journey);
    }
  },
  { immediate: true },
);

const showAll = () => {
  if (currentJourney.value) return;

  streamStates.value.forEach(show);
  componentStates.value.forEach(activate);
};

watch(currentJourney, showAll);
</script>
