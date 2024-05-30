<template>
  <svg
    v-if="isRunning"
    id="display-presentation"
    ref="root"
    width="100%"
    viewBox="0 0 1920 1080"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <InnerWaves />
    <OuterWaves />
    <PhaseLanes />
    <MapLegend v-show="showWidgets" />
    <FZLogo />
    <PipeLines />
    <PipeStreams />
    <Suspense>
      <PowerHubComponents />
    </Suspense>
  </svg>
</template>

<script setup lang="ts">
import MapLegend from "./presentation/MapLegend.vue";
import FZLogo from "./presentation/FZLogo.vue";
import InnerWaves from "./presentation/InnerWaves.vue";
import OuterWaves from "./presentation/OuterWaves.vue";
import PhaseLanes from "./presentation/PhaseLanes.vue";
import PipeLines from "./presentation/PipeLines.vue";
import PipeStreams from "./presentation/PipeStreams.vue";
import PowerHubComponents from "./presentation/PowerHubComponents.vue";

import { usePresentationStore } from "@/stores/presentation";
import type { Journey } from "@/types";
import { useSleep, activate, deactivate, mute, unmute, startFlow, stopFlow } from "@/utils";
import { onMounted, onDeactivated, ref } from "vue";
import { toRefs } from "vue";
import { zip } from "lodash";

const COMPONENT_ANIMATION_IN_MS = 750;
const isRunning = ref(false);
const sleep = useSleep(isRunning);

const { startSlideShow, stopSlideShow, getFlow, setJourney } = usePresentationStore();
const { componentStates, streamStates, root, showWidgets, showWaves, pipes } =
  toRefs(usePresentationStore());

const activateStream = async (journey: Journey) => {
  const { streams, components } = getFlow(journey);

  for (let [component, stream] of zip(components, streams)) {
    if (component) {
      component.active = true;
      component.highlighted = true;

      await sleep(COMPONENT_ANIMATION_IN_MS);

      component.highlighted = false;
    }

    if (stream) {
      stream.active = true;
      await sleep(500);
    }
  }
};

const deactivateAll = async (nextJourney: Journey) => {
  const { components } = getFlow(nextJourney);

  componentStates.value.forEach(deactivate);
  activate(components[0]);

  streamStates.value.forEach(mute);

  await sleep(COMPONENT_ANIMATION_IN_MS);

  streamStates.value.forEach(deactivate);
  streamStates.value.forEach(unmute);
  streamStates.value.forEach(stopFlow);
};

const hideAll = (nextJourney: Journey) => {
  componentStates.value.forEach(mute);
  const { components } = getFlow(nextJourney);
  components.forEach(unmute);
  pipes.value.active = false;
};

const showAll = () => {
  componentStates.value.forEach(unmute);
  pipes.value.active = true;
};

const toggleWaves = async (show: boolean) => {
  showWaves.value = show;
  await sleep(show ? 500 : 1000);
};

const toggleWidgets = async (show: boolean) => {
  showWidgets.value = show;
  await sleep(400);
};

const activateAllComponents = () => {
  componentStates.value.forEach(activate);
};

const startWaterFlow = (journey: Journey) => {
  const { streams } = getFlow(journey);
  streams.forEach(startFlow);
};

const start = async () => {
  if (!isRunning.value) return;

  try {
    toggleWidgets(true);
    activateAllComponents();
    await sleep(5000);
    setJourney("electrical");
    await deactivateAll("electrical");
    await activateStream("electrical");
    await sleep(3000);
    await toggleWidgets(false);
    hideAll("electrical");
    await toggleWaves(false);
    await startSlideShow("electrical");
    showAll();
    await toggleWaves(true);
    await toggleWidgets(true);
    setJourney("heat");
    await deactivateAll("heat");
    await activateStream("heat");
    await sleep(3000);
    await toggleWidgets(false);
    hideAll("heat");
    await toggleWaves(false);
    await startSlideShow("heat");
    showAll();
    await toggleWaves(true);
    await toggleWidgets(true);
    setJourney("water");
    await deactivateAll("water");
    await activateStream("water");
    startWaterFlow("water");
    await sleep(5000);
    await toggleWidgets(false);
    hideAll("water");
    await toggleWaves(false);
    await startSlideShow("water");
    showAll();
    await toggleWaves(true);
    await toggleWidgets(true);

    deactivateAll("electrical");

    setTimeout(start);
  } catch (e) {
    if (e !== "aborted") {
      console.log(e);
    }
  }
};

onMounted(() => {
  isRunning.value = true;
  setTimeout(start);
});

onDeactivated(() => {
  isRunning.value = false;
  stopSlideShow();
});
</script>
