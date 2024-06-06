import type { Journey, PresentationAction } from "@/types";
import {
  activate,
  deactivate,
  dehighlight,
  hide,
  highlight,
  reset,
  show,
  stopFlow,
  unmute,
} from "@/utils";
import { zip } from "lodash";
import { toRefs } from "vue";

const COMPONENT_ANIMATION_IN_MS = 750;

export const actionFn = (action: PresentationAction) => action;

export const sleep = (duration?: number) => actionFn(async ({ sleep }) => await sleep(duration));

export const deactivateAll = (nextJourney: Journey) =>
  actionFn(async ({ getFlow, componentStates, streamStates, sleep }) => {
    const { components } = getFlow(nextJourney);

    componentStates.forEach(deactivate);
    activate(components[0]);

    streamStates.forEach(hide);

    await sleep(COMPONENT_ANIMATION_IN_MS);

    streamStates.forEach(deactivate);
    streamStates.forEach(stopFlow);
  });

export const activateStream = (journey: Journey) =>
  actionFn(async ({ getFlow, sleep }) => {
    const { streams, components } = getFlow(journey);

    for (const [component, stream] of zip(components, streams)) {
      if (!component) return;

      activate(component);
      highlight(component);

      await sleep(COMPONENT_ANIMATION_IN_MS);

      dehighlight(component);

      if (stream && !stream.skip) {
        show(stream);
        activate(stream);
        await sleep(500);
      }
    }
  });

export const hideAll = (nextJourney: Journey) =>
  actionFn(({ componentStates, getFlow, pipes }) => {
    componentStates.forEach(hide);
    const { components } = getFlow(nextJourney);
    components.forEach(show);
    deactivate(pipes);
  });

export const showAll = actionFn(({ componentStates, pipes }) => {
  componentStates.forEach(show);
  activate(pipes);
});

export const toggleWaves = (show: boolean) =>
  actionFn(async (store, { showWaves } = toRefs(store)) => {
    showWaves.value = show;
    await store.sleep(show ? 500 : 1000);
  });

export const toggleWidgets = (show: boolean) =>
  actionFn(async (store, { showWidgets } = toRefs(store)) => {
    showWidgets.value = show;
    await store.sleep(400);
  });

export const activateAllComponents = actionFn(({ componentStates }) =>
  componentStates.forEach(activate),
);

export const resetAll = actionFn(({ pipes, componentStates, streamStates }) => {
  componentStates.forEach(reset);
  streamStates.forEach(reset);
  unmute(pipes);
});
