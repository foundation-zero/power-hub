<template>
  <component :is="view" />
</template>

<script setup lang="ts">
import { useDisplay } from "vuetify";
import { computed, watch } from "vue";
import { defineAsyncComponent } from "vue";
import { toRefs } from "vue";
import { usePresentationStore } from "@/stores/presentation";
import { activate, show } from "@/utils";

const PortraitView = defineAsyncComponent(() => import("./PortraitView.vue"));
const LandscapeView = defineAsyncComponent(() => import("./LandscapeView.vue"));

const { mdAndUp, width, height } = useDisplay();
const { currentJourney, componentStates, streamStates } = toRefs(usePresentationStore());

const view = computed(() => {
  if (mdAndUp.value && width.value > height.value) {
    return LandscapeView;
  }

  return PortraitView;
});

const showAll = () => {
  if (currentJourney.value) return;

  streamStates.value.forEach(show);
  componentStates.value.forEach(activate);
};

watch(currentJourney, showAll);
</script>
